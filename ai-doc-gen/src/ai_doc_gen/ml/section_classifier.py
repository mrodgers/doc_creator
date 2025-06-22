"""
Machine Learning-based Section Classifier

This module provides ML-powered section classification for improved accuracy
in document processing and template matching.
"""

import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import logging

logger = logging.getLogger(__name__)


class SectionClassifier:
    """Machine Learning-based section classifier for technical documentation."""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the section classifier."""
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            stop_words='english',
            min_df=2,
            max_df=0.95
        )
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.classes = [
            'overview', 'specification', 'installation', 'configuration',
            'requirements', 'features', 'safety', 'maintenance',
            'troubleshooting', 'appendix', 'other'
        ]
        self.model_path = model_path or 'models/section_classifier.pkl'
        self.is_trained = False
        
        # Load pre-trained model if available
        self._load_model()
    
    def _load_model(self) -> None:
        """Load pre-trained model if available."""
        try:
            if Path(self.model_path).exists():
                model_data = joblib.load(self.model_path)
                self.vectorizer = model_data['vectorizer']
                self.classifier = model_data['classifier']
                self.classes = model_data['classes']
                self.is_trained = True
                logger.info(f"Loaded pre-trained model from {self.model_path}")
        except Exception as e:
            logger.warning(f"Could not load pre-trained model: {e}")
    
    def _save_model(self) -> None:
        """Save the trained model."""
        try:
            Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
            model_data = {
                'vectorizer': self.vectorizer,
                'classifier': self.classifier,
                'classes': self.classes
            }
            joblib.dump(model_data, self.model_path)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def prepare_training_data(self) -> Tuple[List[str], List[str]]:
        """Prepare training data for the classifier."""
        # Technical documentation section examples
        training_data = {
            'overview': [
                'product overview', 'introduction', 'about this guide', 'getting started',
                'what is', 'overview of', 'product description', 'general information',
                'system overview', 'architecture overview', 'component overview'
            ],
            'specification': [
                'technical specifications', 'product specifications', 'hardware specifications',
                'system requirements', 'technical requirements', 'specifications',
                'technical details', 'product details', 'hardware details',
                'performance specifications', 'capacity specifications'
            ],
            'installation': [
                'installation guide', 'installation procedures', 'installation steps',
                'how to install', 'installation requirements', 'installation process',
                'setup guide', 'deployment guide', 'installation instructions',
                'hardware installation', 'software installation'
            ],
            'configuration': [
                'configuration guide', 'configuration procedures', 'configuration steps',
                'how to configure', 'configuration settings', 'setup configuration',
                'initial configuration', 'advanced configuration', 'configuration options',
                'system configuration', 'network configuration'
            ],
            'requirements': [
                'system requirements', 'hardware requirements', 'software requirements',
                'prerequisites', 'requirements', 'minimum requirements',
                'recommended requirements', 'environmental requirements',
                'power requirements', 'space requirements'
            ],
            'features': [
                'product features', 'key features', 'main features', 'capabilities',
                'functionality', 'characteristics', 'properties', 'benefits',
                'feature overview', 'product capabilities', 'system features'
            ],
            'safety': [
                'safety warnings', 'safety precautions', 'safety requirements',
                'safety guidelines', 'safety information', 'warning notices',
                'precautions', 'safety procedures', 'safety instructions',
                'hazard warnings', 'safety considerations'
            ],
            'maintenance': [
                'maintenance procedures', 'maintenance guide', 'maintenance instructions',
                'preventive maintenance', 'routine maintenance', 'maintenance schedule',
                'maintenance requirements', 'service procedures', 'maintenance tasks',
                'upkeep procedures', 'maintenance checklist'
            ],
            'troubleshooting': [
                'troubleshooting guide', 'troubleshooting procedures', 'problem solving',
                'diagnostic procedures', 'troubleshooting steps', 'common problems',
                'error messages', 'diagnostics', 'troubleshooting tips',
                'problem resolution', 'troubleshooting checklist'
            ],
            'appendix': [
                'appendix', 'appendices', 'reference information', 'reference data',
                'technical reference', 'glossary', 'acronyms', 'abbreviations',
                'reference tables', 'reference charts', 'additional information'
            ],
            'other': [
                'miscellaneous', 'additional information', 'notes', 'comments',
                'general information', 'background information', 'context',
                'related information', 'supporting information'
            ]
        }
        
        texts = []
        labels = []
        
        for label, examples in training_data.items():
            for example in examples:
                texts.append(example)
                labels.append(label)
        
        return texts, labels
    
    def train(self, custom_data: Optional[Tuple[List[str], List[str]]] = None) -> Dict[str, float]:
        """Train the section classifier."""
        logger.info("Training section classifier...")
        
        # Prepare training data
        if custom_data:
            texts, labels = custom_data
        else:
            texts, labels = self.prepare_training_data()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        # Vectorize text
        X_train_vectors = self.vectorizer.fit_transform(X_train)
        X_test_vectors = self.vectorizer.transform(X_test)
        
        # Train classifier
        self.classifier.fit(X_train_vectors, y_train)
        
        # Evaluate
        y_pred = self.classifier.predict(X_test_vectors)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Generate detailed report
        report = classification_report(y_test, y_pred, output_dict=True)
        
        self.is_trained = True
        self._save_model()
        
        logger.info(f"Training completed. Accuracy: {accuracy:.3f}")
        
        return {
            'accuracy': accuracy,
            'classification_report': report
        }
    
    def classify_section(self, heading: str, content: List[str] = None) -> Dict[str, Any]:
        """Classify a section based on its heading and content."""
        if not self.is_trained:
            logger.warning("Classifier not trained. Training with default data...")
            self.train()
        
        # Combine heading and content for classification
        text = heading
        if content:
            text += " " + " ".join(content[:3])  # Use first 3 content items
        
        # Vectorize
        text_vector = self.vectorizer.transform([text])
        
        # Predict
        prediction = self.classifier.predict(text_vector)[0]
        probabilities = self.classifier.predict_proba(text_vector)[0]
        
        # Get confidence scores
        confidence_scores = dict(zip(self.classifier.classes_, probabilities))
        
        return {
            'predicted_class': prediction,
            'confidence': confidence_scores[prediction],
            'all_probabilities': confidence_scores,
            'text_analyzed': text[:100] + "..." if len(text) > 100 else text
        }
    
    def classify_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify multiple sections."""
        classified_sections = []
        
        for section in sections:
            heading = section.get('heading', '')
            content = section.get('content', [])
            
            classification = self.classify_section(heading, content)
            
            classified_section = {
                **section,
                'ml_classification': classification,
                'predicted_type': classification['predicted_class'],
                'classification_confidence': classification['confidence']
            }
            
            classified_sections.append(classified_section)
        
        return classified_sections
    
    def get_classification_insights(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get insights from section classifications."""
        if not sections:
            return {}
        
        # Classify all sections
        classified_sections = self.classify_sections(sections)
        
        # Analyze classifications
        class_counts = {}
        confidence_scores = []
        high_confidence_sections = []
        
        for section in classified_sections:
            classification = section.get('ml_classification', {})
            predicted_class = classification.get('predicted_class', 'unknown')
            confidence = classification.get('confidence', 0.0)
            
            # Count classes
            class_counts[predicted_class] = class_counts.get(predicted_class, 0) + 1
            
            # Track confidence scores
            confidence_scores.append(confidence)
            
            # Track high confidence sections
            if confidence > 0.8:
                high_confidence_sections.append({
                    'heading': section.get('heading', ''),
                    'predicted_class': predicted_class,
                    'confidence': confidence
                })
        
        # Calculate statistics
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        min_confidence = np.min(confidence_scores) if confidence_scores else 0.0
        max_confidence = np.max(confidence_scores) if confidence_scores else 0.0
        
        return {
            'total_sections': len(sections),
            'class_distribution': class_counts,
            'confidence_statistics': {
                'average': avg_confidence,
                'minimum': min_confidence,
                'maximum': max_confidence
            },
            'high_confidence_sections': high_confidence_sections,
            'classification_coverage': len(class_counts) / len(self.classes)
        }


class SectionClassifierFactory:
    """Factory for creating section classifiers."""
    
    @staticmethod
    def create_classifier(model_type: str = 'random_forest', **kwargs) -> SectionClassifier:
        """Create a section classifier of the specified type."""
        if model_type == 'random_forest':
            return SectionClassifier(**kwargs)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    @staticmethod
    def create_ensemble_classifier() -> 'EnsembleSectionClassifier':
        """Create an ensemble classifier for improved accuracy."""
        return EnsembleSectionClassifier()


class EnsembleSectionClassifier:
    """Ensemble classifier combining multiple ML models for improved accuracy."""
    
    def __init__(self):
        """Initialize the ensemble classifier."""
        self.classifiers = []
        self.weights = []
        self.is_trained = False
    
    def add_classifier(self, classifier: SectionClassifier, weight: float = 1.0):
        """Add a classifier to the ensemble."""
        self.classifiers.append(classifier)
        self.weights.append(weight)
    
    def classify_section(self, heading: str, content: List[str] = None) -> Dict[str, Any]:
        """Classify a section using ensemble voting."""
        if not self.classifiers:
            raise ValueError("No classifiers in ensemble")
        
        predictions = []
        confidences = []
        
        for classifier, weight in zip(self.classifiers, self.weights):
            result = classifier.classify_section(heading, content)
            predictions.append((result['predicted_class'], weight))
            confidences.append(result['confidence'] * weight)
        
        # Weighted voting
        class_votes = {}
        for pred_class, weight in predictions:
            class_votes[pred_class] = class_votes.get(pred_class, 0) + weight
        
        # Get winning prediction
        predicted_class = max(class_votes.items(), key=lambda x: x[1])[0]
        ensemble_confidence = np.mean(confidences)
        
        return {
            'predicted_class': predicted_class,
            'confidence': ensemble_confidence,
            'ensemble_votes': class_votes,
            'individual_predictions': [
                {
                    'classifier_id': i,
                    'prediction': pred[0],
                    'confidence': conf
                }
                for i, (pred, conf) in enumerate(zip(predictions, confidences))
            ]
        } 