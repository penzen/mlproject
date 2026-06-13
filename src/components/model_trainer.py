# Basic imports
import os
import sys
from dataclasses import dataclass

from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

from src.exception import CustomException
from src.logger import logging
from src.utils import save_object


@dataclass
class ModelTrainerConfig:
    trained_model_file_path = os.path.join("artifacts", "model.pkl")


class ModelTrainer:
    def __init__(self):
        self.model_trainer_config = ModelTrainerConfig()

    def initialize_model_trainer_config(self, train_array, test_array):
        try:
            logging.info("Splitting training and test input data")

            X_train = train_array[:, :-1]
            y_train = train_array[:, -1]
            X_test = test_array[:, :-1]
            y_test = test_array[:, -1]

            logging.info("Training Ridge Regression model")

            model = Ridge()
            model.fit(X_train, y_train)

            predictions = model.predict(X_test)
            r2_square = r2_score(y_test, predictions)

            logging.info(f"Ridge Regression R2 score: {r2_square}")

            if r2_square < 0.6:
                raise CustomException("Model score is below acceptable threshold", sys)

            logging.info("Saving trained Ridge model")

            save_object(
                file_path=self.model_trainer_config.trained_model_file_path,
                obj=model
            )

            return r2_square

        except Exception as e:
            raise CustomException(e, sys)

