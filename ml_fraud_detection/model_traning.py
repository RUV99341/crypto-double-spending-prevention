from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_model(dataset_path):
    # Load dataset
    data = ...  # Add dataset loading logic
    X, y = data.drop("label", axis=1), data["label"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    joblib.dump(model, "ml_fraud_detection/fraud_detection_model.pkl")