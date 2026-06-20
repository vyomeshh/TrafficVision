# 🚦 TrafficVision AI

**TrafficVision AI** is an advanced, automated traffic violation detection system. It leverages cutting-edge Computer Vision models to process traffic camera images and identify multiple types of violations simultaneously.

The system features a highly interactive React frontend with a 3D flip-card UI, backed by a robust FastAPI Python service that runs YOLOv8 and PaddleOCR pipelines.

---

## 🌟 Key Features

1. **YOLOv8 Object Detection**: Identifies Cars, Motorcycles, Buses, Trucks, and Persons.
2. **PaddleOCR License Plate Recognition**: Extracts readable text from detected license plates.
3. **Automated Violation Heuristics**:
   - 🏍️ **Triple Riding**: Uses AABB bounding-box intersection to detect 3 or more people on a single motorcycle.
   - ⛑️ **No Helmet Detection**: Analyzes the top region of riders' bounding boxes using HSV color variance heuristics to estimate helmet presence.
   - 🛑 **Red Light Violation**: Checks if vehicles have crossed a configurable Y-axis stop line.
4. **Interactive 3D UI**: The frontend utilizes a seamless 3D flip-card animation to process uploads and immediately reveal AI-annotated results on the back face.
5. **Real-time Logging**: Displays the backend Python inference logs directly in the frontend UI.
6. **Robust Persistence**: Persists detections to a PostgreSQL database (with an automatic fallback to SQLite) without rejecting multiple violations for the same image.

---

## 🏗️ Tech Stack

### Frontend
- **React.js (Vite)**
- **Tailwind CSS**
- **Lucide React** (Icons)
- **Recharts** (Analytics)

### Backend
- **FastAPI** (Python 3.10+)
- **Ultralytics YOLOv8** (Object Detection)
- **PaddleOCR** (Optical Character Recognition)
- **OpenCV** (Image processing & CLAHE enhancement)
- **SQLAlchemy** (Database ORM for Postgres & SQLite)

---

## 🚀 Getting Started

### Prerequisites
- Node.js (v18+)
- Python 3.10+
- PostgreSQL (Optional, defaults to SQLite)

### 1. Start the Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up the `.env` file (optional, defaults are provided):
   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/trafficvision
   YOLO_MODEL=yolov8s.pt
   YOLO_CONFIDENCE=0.20
   STOP_LINE_RATIO=0.7
   ```
5. Run the FastAPI server:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
   ```

### 2. Start the Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to `http://localhost:5173`.

---

## 🧠 How the Pipeline Works

1. **Upload**: An image is uploaded via the frontend.
2. **Pre-processing**: The backend applies CLAHE enhancement, denoising, and motion blur correction for OCR. *(Note: YOLO detection is run on the raw image to preserve edge features and ensure highly occluded objects are detected).*
3. **Detection**: YOLOv8 extracts bounding boxes for all vehicles and persons.
4. **Analysis**: The heuristic engine calculates intersections (IoU and AABB) to map persons to motorcycles and flags violations based on position and region analysis.
5. **OCR**: PaddleOCR extracts license plate text for flagged vehicles.
6. **Annotation**: OpenCV draws bounding boxes and labels onto the image.
7. **Response**: The frontend 3D card flips to reveal the results and auto-switches to the annotated image tab.

---

## 🛡️ License

This project is licensed under the MIT License.
