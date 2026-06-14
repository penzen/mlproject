from flask import Flask, render_template, request, jsonify
import joblib
import numpy as np
import pandas as pd 

from sklearn.preprocessing import StandardScaler
from src.pipeline.prediction_pipeline import CustomData, PredictionPipeline

application = Flask(__name__)

app = application


@app.route('/')
def index():
    return render_template('index.html')




@app.route('/predictdata', methods=['GET','POST'])
def predict_datapoint(): # get this from the home page and then we will use it to make a prediction
    if request.method == 'GET':
        return render_template('home.html') # simple inputs for the features that we will have in the page 
    else: 
        data = CustomData( 
            gender=request.form['gender'],
            race_ethnicity=request.form['race_ethnicity'],
            parental_level_of_education=request.form['parental_level_of_education'],
            lunch=request.form['lunch'],
            test_preparation_course=request.form['test_preparation_course'],
            reading_score=int(request.form['reading_score']),
            writing_score=int(request.form['writing_score']) )
        
        
        
        pred_df = data.get_data_as_dataframe() # we will get the data as a dataframe and then we will use it to make a prediction
        print(pred_df)

        predict_pipeline = PredictionPipeline() # we will use the predict pipeline to make a prediction
        result = predict_pipeline.predict(pred_df) # we will use the predict method to make a

        return render_template('home.html', result=result[0]) # we will return the result to the home page and then we will display it there


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)