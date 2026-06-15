## End to End MAchine Learning Project

1. Docker Build checked
2. Github Workflow
3. Iam User In AWS

## Docker Setup In EC2 commands to be Executed

#optinal

sudo apt-get update -y

sudo apt-get upgrade

#required

curl -fsSL https://get.docker.com -o get-docker.sh

sudo sh get-docker.sh

sudo usermod -aG docker ubuntu

newgrp docker

## Configure EC2 as self-hosted runner:

## Setup github secrets:

AWS_ACCESS_KEY_ID=

AWS_SECRET_ACCESS_KEY=

AWS_REGION = us-east-1

AWS_ECR_LOGIN_URI = demo>>  566373416292.dkr.ecr.ap-south-1.amazonaws.com

ECR_REPOSITORY_NAME = simple-app




# MLOps Deployment Section Report: Flask ML App, Docker, CI/CD, AWS ECR, EC2

## 1. Overview

In this section, I took a machine learning Flask application and moved it step by step toward a real MLOps-style deployment workflow.

The project started as a local Flask app that loads a trained model and preprocessor, accepts user input through an HTML form, and returns a student performance prediction. From there, I worked through cloud deployment, dependency issues, Docker containerization, GitHub Actions CI/CD, AWS ECR, EC2, and self-hosted GitHub runners.

The main goal was not only to make the app run, but to understand the full deployment chain:

```text
Local ML app
→ GitHub repository
→ Docker image
→ Container registry
→ Cloud server
→ CI/CD automation
→ Running web app
```

---

## 2. Project Context

The application is a student performance prediction app built with Flask and scikit-learn.

The app uses:

```text
application.py
templates/
src/
artifacts/model.pkl
artifacts/preprocessor.pkl
requirements.txt
Dockerfile
GitHub Actions workflow
```

The prediction flow is:

```text
User opens web page
→ fills student information
→ Flask receives form data
→ CustomData converts input into a DataFrame
→ PredictionPipeline loads preprocessor.pkl and model.pkl
→ model predicts math score
→ result is displayed on the page
```

The final saved model was checked locally and found to be:

```text
<class 'sklearn.linear_model._ridge.Ridge'>
```

This was an important discovery because it meant the deployed application did not need heavy training libraries such as CatBoost or XGBoost.

---

## 3. Elastic Beanstalk Deployment Attempt

Before moving fully into Docker, I deployed the Flask app using AWS Elastic Beanstalk and CodePipeline.

The initial flow was:

```text
GitHub
→ CodePipeline
→ Elastic Beanstalk
→ EC2 behind Elastic Beanstalk
→ Flask app served by Gunicorn
```

The Elastic Beanstalk environment eventually reached:

```text
Health: OK
```

and the application worked successfully.

However, getting there involved multiple deployment problems.

---

## 4. Mistake 1: Wrong or Old CodePipeline Artifact

At one point, Elastic Beanstalk kept failing with:

```text
ModuleNotFoundError: No module named 'flask'
```

At first this looked like a simple missing dependency problem. But `Flask` had already been added to `requirements.txt`.

After checking the CodePipeline artifact, I discovered that the downloaded artifact did not contain the latest `requirements.txt`. This meant the pipeline was not deploying the latest version of the repository.

Important lesson:

```text
A successful GitHub push does not always mean the deployment stage is using the expected artifact.
```

I learned to inspect the actual CodePipeline source artifact by downloading it from S3, renaming it to `.zip`, extracting it, and checking whether it contained the expected files.

---

## 5. Mistake 2: Pipeline Source and Deploy Revision Mismatch

The CodePipeline UI showed the Source stage using the latest commit, but the Deploy stage appeared to reference an older deployment config commit.

This created confusion because the pipeline looked successful, but Elastic Beanstalk was still not receiving the correct dependencies.

The fix was to create a completely new pipeline with the correct GitHub source and deployment configuration.

Lesson learned:

```text
If a CI/CD pipeline becomes confusing or appears to be using the wrong artifact, recreating the pipeline cleanly can be faster than debugging a broken configuration for hours.
```

---

## 6. Mistake 3: Missing IAM Permissions for the New Pipeline

After creating the new pipeline, the deployment failed with a role permission error:

```text
The provided role does not have the elasticbeanstalk:CreateApplicationVersion permission
```

This happened because the new pipeline had a new CodePipeline service role. Permissions added to the old pipeline role did not apply to the new role.

The fix was to add an inline IAM policy to the new CodePipeline role with permissions for Elastic Beanstalk deployment.

Lesson learned:

```text
Every AWS service that performs actions on your behalf uses a role.
If you recreate the service, you may also create a new role.
That new role needs its own permissions.
```

---

## 7. Mistake 4: Dependency Installation Failed Due to Disk Space

After fixing the source and IAM issues, Elastic Beanstalk started reading the latest `requirements.txt`, but deployment failed during dependency installation.

The important error was:

```text
ERROR: Could not install packages due to an OSError: [Errno 28] No space left on device
```

The cause was that the deployment dependencies were too heavy. The requirements included packages such as:

```text
catboost
xgboost
```

`xgboost` pulled a very large dependency:

```text
nvidia-nccl-cu12
```

This consumed too much disk space on the Elastic Beanstalk EC2 instance.

The key realization was that the deployed app only needed inference dependencies, not all training dependencies.

Since the final model was Ridge Regression, the deployment dependencies were reduced to:

```text
Flask
gunicorn
numpy
pandas
scikit-learn
dill
```

Lesson learned:

```text
Training dependencies and deployment dependencies are not always the same.
A production inference app should only include what it needs to load the model and make predictions.
```

---

## 8. Branching Strategy

Before removing heavy training-related code and dependencies from the deployment version, I created a separate branch to preserve the full training version.

The idea was:

```text
main
→ lightweight deployment version

full-training-version
→ full training/experimentation version
```

This made it safe to simplify the main branch without losing the original training code.

Lesson learned:

```text
Branches are useful for separating experiment/training code from production/deployment code.
```

---

## 9. Removing Unnecessary Artifacts

The project contained a folder:

```text
catboost_info/
```

This folder was created automatically by CatBoost during training.

Since the final deployed model was Ridge Regression and CatBoost was not needed for deployment, the folder was removed from the deployment branch and added to `.gitignore`.

Lesson learned:

```text
Training artifacts should not be shipped with a lightweight production deployment unless they are required at runtime.
```

---

## 10. Dockerizing the Flask App

After Elastic Beanstalk worked, I moved to Docker.

The purpose of Docker was to package the app with its runtime environment so it can run consistently anywhere.

The final Dockerfile used was:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "application:application"]
```

Important choices:

```text
python:3.11-slim
→ safer for ML packages than Python 3.13

COPY requirements.txt first
→ allows Docker layer caching for dependency installs

gunicorn
→ production-style WSGI server instead of Flask debug server

application:application
→ points to application.py and the Flask variable named application
```

---

## 11. Dockerfile Mistakes Fixed

The first Dockerfile had a few issues:

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . /app

RUN apt update -y && apt install awscli -y

RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

Problems:

```text
1. The file was application.py, not app.py
2. Python 3.13 could create compatibility issues with ML packages
3. AWS CLI was unnecessary inside the image
4. Flask development server was less appropriate than Gunicorn
```

The corrected Dockerfile solved these problems.

Lesson learned:

```text
The Docker CMD must match the actual Python file and Flask application variable.
```

---

## 12. Docker Image vs Container

I learned the difference between a Docker image and a Docker container.

```text
Docker image
= packaged blueprint of the app

Docker container
= running instance of that image
```

Analogy:

```text
Image = recipe
Container = cooked meal

Image = class
Container = object instance
```

For this project:

```text
student-performance-app
= Docker image

running container on port 5000
= live Flask app
```

---

## 13. Testing Docker Locally

The local Docker workflow was:

```bash
docker build -t student-performance-app .
docker run -p 5000:5000 student-performance-app
```

This mapped:

```text
localhost:5000 on my machine
→ port 5000 inside the container
```

The app was then accessible at:

```text
http://localhost:5000/
http://localhost:5000/predictdata
```

A common confusion was seeing Gunicorn print:

```text
Listening at: http://0.0.0.0:5000
```

At first, I tried opening:

```text
http://0.0.0.0:5000/
```

That failed with:

```text
ERR_ADDRESS_INVALID
```

The correct browser URL was:

```text
http://localhost:5000/
```

Lesson learned:

```text
0.0.0.0 means "listen on all interfaces" inside the container.
It is not the address to open in the browser.
Use localhost or 127.0.0.1 from the host machine.
```

---

## 14. Debugging Inside the Docker Container

To inspect the container filesystem, I ran:

```bash
docker run -it student-performance-app sh
```

Inside the container, I checked:

```bash
ls templates
```

and confirmed:

```text
home.html
index.html
```

This proved that the templates were copied correctly into the Docker image.

I also learned that inside the container shell:

```text
# 
```

means I am inside a Linux shell, not Windows CMD.

To exit:

```bash
exit
```

Also:

```text
cls
```

does not work in Linux. The Linux equivalent is:

```bash
clear
```

Lesson learned:

```text
Docker containers run Linux environments, so Windows commands may not work inside them.
```

---

## 15. GitHub Actions and CI/CD

After Docker worked locally, I moved toward CI/CD with GitHub Actions.

CI/CD means:

```text
Continuous Integration
→ automatically check/build/test the project

Continuous Delivery/Deployment
→ automatically package and deploy the app
```

GitHub Actions runs workflow files stored in:

```text
.github/workflows/
```

The workflow is triggered when code is pushed to a branch.

Important branch lesson:

```text
If the workflow says branches: [main], it only runs on main.
If I am working on another branch, I must either push to main or update the workflow trigger to that branch.
```

---

## 16. GitHub Runner

I learned about GitHub runners.

A runner is the machine that executes GitHub Actions jobs.

There are two types:

```text
GitHub-hosted runner
→ temporary machine provided by GitHub, such as ubuntu-latest

Self-hosted runner
→ my own machine/server, such as an EC2 instance
```

I configured a self-hosted runner on EC2 using a command like:

```bash
./config.sh --url https://github.com/penzen/mlproject --token <runner-token>
```

Then the runner can be started using:

```bash
./run.sh
```

Important lesson:

```text
GitHub Actions is the automation system.
The runner is the machine that actually runs the workflow commands.
```

---

## 17. EC2 and ECR

I created:

```text
EC2 instance
→ cloud server where the app can run

ECR private repository
→ private AWS storage for Docker images
```

The relationship is:

```text
Docker image is built
→ pushed to ECR
→ EC2 pulls image from ECR
→ EC2 runs image as a container
```

Simple mapping:

```text
GitHub = stores code
ECR = stores Docker images
EC2 = runs Docker containers
```

---

## 18. CI/CD Workflow With ECR and EC2

The CI/CD workflow pattern became:

```text
Push code to GitHub
→ GitHub Actions starts
→ CI job runs basic checks
→ Docker image is built
→ image is pushed to ECR
→ self-hosted EC2 runner pulls latest image
→ old container is stopped
→ new container is started
```

The workflow had three main jobs:

```text
1. Continuous Integration
2. Build and Push Docker Image to ECR
3. Deploy to EC2 Self-Hosted Runner
```

---

## 19. Mistake 5: Wrong ECR Image Pull Path

The first CI/CD run almost worked:

```text
Continuous Integration ✅
Build and Push Docker Image to ECR ✅
Deploy to EC2 Self-Hosted Runner ❌
```

The deployment failed at:

```text
docker pull ***/***:latest
```

with:

```text
image not found
```

This meant the EC2 runner tried to pull an image path that did not match the image pushed to ECR.

The likely issue was the manually configured secret:

```text
AWS_ECR_LOGIN_URI
```

The better approach was to use the ECR login step output:

```yaml
${{ steps.login-ecr.outputs.registry }}
```

instead of manually constructing the registry URL.

Lesson learned:

```text
If Docker push succeeds but Docker pull fails, check that the image registry URI, repository name, region, and tag match exactly.
```

---

## 20. Port Mapping on EC2

The Docker container listens internally on port 5000:

```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "application:application"]
```

But on EC2, I can expose it using:

```bash
docker run -d -p 8080:5000 --name mltest IMAGE_NAME
```

This means:

```text
EC2 public port 8080
→ container port 5000
```

So the EC2 security group must allow inbound traffic on port:

```text
8080
```

Then the app can be opened using:

```text
http://EC2_PUBLIC_IP:8080
```

Alternative:

```bash
-p 80:5000
```

would allow:

```text
http://EC2_PUBLIC_IP
```

but for learning, port 8080 is clearer.

Lesson learned:

```text
The app port, container port, Docker mapped port, and EC2 security group port must line up.
```

---

## 21. Azure Concept Introduction

The instructor then introduced Azure.

The Azure flow was:

```text
Web app
→ Docker image
→ private image
→ Azure Container Registry
→ Azure Web App pulls and runs the image
```

This maps closely to AWS:

```text
AWS ECR
= Azure Container Registry

AWS EC2
= Azure Virtual Machine

AWS App Runner / ECS / Elastic Beanstalk
= Azure Web App / Azure Container Apps
```

The big lesson is that cloud providers use different names, but the MLOps deployment pattern is the same:

```text
Code
→ Docker image
→ private registry
→ cloud runtime
→ CI/CD automation
```

---

## 22. Key Commands Used

### Docker

```bash
docker build -t student-performance-app .
docker build --no-cache -t student-performance-app .
docker run -p 5000:5000 student-performance-app
docker run -it student-performance-app sh
docker ps
docker stop <container_id>
docker rm <container_id>
docker system prune -f
```

### Git

```bash
git status
git branch
git checkout -b full-training-version
git push origin full-training-version
git checkout main
git add .
git commit -m "message"
git push origin branch-name
```

### GitHub Runner

```bash
cd actions-runner
./run.sh
```

Optional service setup:

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

---

## 23. Most Important Lessons Learned

### 1. Deployment is different from training

Training code can use many packages:

```text
CatBoost
XGBoost
matplotlib
RandomizedSearchCV
many model candidates
```

But deployment only needs the final model’s runtime dependencies.

Since the final model was Ridge Regression, the lightweight deployment only needed:

```text
Flask
gunicorn
numpy
pandas
scikit-learn
dill
```

### 2. Docker makes the runtime environment repeatable

Instead of hoping the server has the right dependencies, Docker packages the app and runtime together.

### 3. CI/CD has multiple moving parts

A full deployment pipeline may involve:

```text
GitHub workflow
GitHub runner
Docker image
ECR registry
EC2 server
security group
environment variables/secrets
```

A failure in any one part can break deployment.

### 4. Logs are essential

The final answers came from reading logs carefully:

```text
No module named flask
No space left on device
image not found
worker timeout
```

Each error pointed to a different layer of the system.

### 5. Cloud services have equivalent concepts

AWS and Azure use different names, but the architecture is similar:

```text
Registry stores images
Server/app service runs images
CI/CD automates deployment
```

---

## 24. Final Result

By the end of this section, I successfully:

```text
Built a working Flask ML prediction app
Deployed it through Elastic Beanstalk
Debugged CodePipeline artifact issues
Fixed IAM role permissions
Reduced deployment dependencies
Created a Dockerfile
Built and ran the app locally in Docker
Verified routes with curl
Created an ECR private repository
Created an EC2 instance
Configured a self-hosted GitHub runner
Created a GitHub Actions CI/CD workflow
Built and pushed Docker images to ECR
Started debugging automated EC2 deployment
Learned the equivalent Azure container deployment flow
```

---

## 25. Final Reflection

This section was difficult because the errors came from different layers:

```text
Git/GitHub
AWS CodePipeline
Elastic Beanstalk
IAM permissions
Python dependencies
Docker
ECR
EC2
GitHub Actions
Networking ports
```

At first, many errors looked like code problems, but most were actually deployment, dependency, permission, or configuration issues.

The biggest takeaway is that MLOps is not only about training a model. It is about making the model available reliably through software engineering, infrastructure, automation, and debugging.

The final mental model I learned is:

```text
Model training creates the artifact.
Flask serves the model.
Docker packages the app.
ECR stores the image.
EC2 runs the image.
GitHub Actions automates the process.
Logs reveal what is broken.
```

This section gave me a much clearer understanding of how real ML applications move from local development to cloud deployment.
