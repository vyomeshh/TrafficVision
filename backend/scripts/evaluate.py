import numpy as np
from typing import List, Dict, Any, Tuple

def calculate_iou(boxA: List[int], boxB: List[int]) -> float:
    """Calculate Intersection over Union (IoU) of two bounding boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    iou = interArea / float(boxAArea + boxBArea - interArea) if (boxAArea + boxBArea - interArea) > 0 else 0.0
    return iou

def evaluate_performance(predictions: List[Dict[str, Any]], ground_truths: List[Dict[str, Any]], iou_threshold: float = 0.5) -> Dict[str, float]:
    """
    Evaluates detection performance metrics against ground truth data.
    
    Returns a dictionary containing:
        - True Positives (TP)
        - False Positives (FP)
        - False Negatives (FN)
        - Precision
        - Recall
        - F1-Score
        - Accuracy (estimated)
    """
    # Track which ground truths have been matched
    matched_gt = [False] * len(ground_truths)
    tp = 0
    fp = 0

    # Sort predictions by confidence (highest first) for mAP style matching
    predictions = sorted(predictions, key=lambda x: x.get("confidence", 0.0), reverse=True)

    for pred in predictions:
        pred_box = pred.get("bbox")
        pred_class = pred.get("class_name") or pred.get("type")
        
        best_iou = 0.0
        best_gt_idx = -1
        
        for idx, gt in enumerate(ground_truths):
            if matched_gt[idx]:
                continue
                
            gt_class = gt.get("class_name") or gt.get("type")
            if pred_class != gt_class:
                continue
                
            iou = calculate_iou(pred_box, gt.get("bbox"))
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = idx
                
        if best_iou >= iou_threshold and best_gt_idx != -1:
            tp += 1
            matched_gt[best_gt_idx] = True
        else:
            fp += 1

    fn = sum(1 for matched in matched_gt if not matched)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # Accuracy is difficult in object detection (True Negatives are infinite background).
    # We approximate it by the ratio of correct detections to all entities (TP + FP + FN)
    accuracy = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0

    return {
        "True Positives": tp,
        "False Positives": fp,
        "False Negatives": fn,
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "F1-Score": round(f1_score, 4),
        "Accuracy (Approx)": round(accuracy, 4)
    }

if __name__ == "__main__":
    print("TrafficVision AI - Evaluation Metrics Script")
    print("---------------------------------------------")
    
    # Mock data for demonstration
    mock_preds = [
        {"class_name": "Car", "bbox": [10, 10, 50, 50], "confidence": 0.9},
        {"class_name": "Motorcycle", "bbox": [100, 100, 150, 150], "confidence": 0.8},
        {"type": "No Helmet", "bbox": [100, 100, 150, 150], "confidence": 0.85}
    ]
    
    mock_gts = [
        {"class_name": "Car", "bbox": [12, 12, 48, 48]},
        {"class_name": "Motorcycle", "bbox": [105, 100, 155, 145]},
        {"type": "No Helmet", "bbox": [105, 100, 155, 145]},
        {"class_name": "Person", "bbox": [200, 200, 250, 250]} # Missed by detector (FN)
    ]
    
    results = evaluate_performance(mock_preds, mock_gts, iou_threshold=0.5)
    for k, v in results.items():
        print(f"{k}: {v}")
    
    print("\n[NOTE] Mean Average Precision (mAP) is typically calculated by varying the confidence threshold")
    print("       to generate a Precision-Recall curve, then computing the Area Under Curve (AUC).")
