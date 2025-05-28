import joblib

class FraudDetection:
    def __init__(self, model_path):
        self.model = joblib.load(model_path)

    def detect(self, transaction_features):
        prediction = self.model.predict([transaction_features])
        return prediction == 1