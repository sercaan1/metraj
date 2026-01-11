# Steel Quantity Takeoff

A Python application to extract rebar (reinforcement steel) quantities from DXF/DWG construction drawings.

## Features

- Parse DXF files and extract geometric entities
- Identify rebar elements by layer names and annotations
- Calculate quantities, lengths, and weights
- Support for Turkish and English layer naming conventions

## Setup Instructions

### 1. Install Python

1. Download Python 3.12+ from https://www.python.org/downloads/
2. **IMPORTANT**: Check ✅ "Add Python to PATH" during installation
3. Verify installation:
   ```bash
   python --version
   pip --version
   ```

### 2. Setup Project

```bash
# Navigate to project folder
cd steel-takeoff

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. VS Code Setup

1. Open the project folder in VS Code
2. Install extensions:
   - Python (Microsoft)
   - Pylance (Microsoft)
3. VS Code should auto-detect the virtual environment
4. Select interpreter: Ctrl+Shift+P → "Python: Select Interpreter" → Choose `venv`

### 4. Run the Application

```bash
# Explore a DXF file first
python explore_dxf.py your_drawing.dxf

# Run main application
python main.py
```

Or press **F5** in VS Code to debug.

## Converting DWG to DXF

DWG is a proprietary format. To convert:

1. **Using AutoCAD**: File → Save As → DXF
2. **Free tool**: [ODA File Converter](https://www.opendesign.com/guestfiles/oda_file_converter)
   - Download and install
   - Select input folder with DWG files
   - Select output folder
   - Choose DXF format
   - Convert

## Project Structure

```
steel-takeoff/
├── main.py              # Main entry point
├── explore_dxf.py       # Utility to explore DXF structure
├── requirements.txt     # Python dependencies
├── src/
│   ├── __init__.py
│   ├── dxf_parser.py    # DXF file parsing
│   └── rebar_analyzer.py # Rebar identification and analysis
└── .vscode/
    ├── launch.json      # Debug configurations
    └── settings.json    # VS Code settings
```

## How It Works

1. **DXF Parser** reads the file and extracts:
   - LINE entities (straight bars)
   - ARC entities (bends)
   - POLYLINE entities (complex shapes, stirrups)
   - TEXT entities (rebar annotations like "10ø16")

2. **Rebar Analyzer** identifies rebar by:
   - Layer names (e.g., "REBAR", "STEEL", "DONATI")
   - Text annotations (e.g., "10ø16", "ø12/15")
   - Geometric patterns

3. **Output** shows:
   - Diameter
   - Shape (straight, L-shape, U-shape, stirrup)
   - Length
   - Quantity
   - Total weight

## Rebar Unit Weights

| Diameter | Weight (kg/m) |
|----------|---------------|
| ø8       | 0.395         |
| ø10      | 0.617         |
| ø12      | 0.888         |
| ø14      | 1.208         |
| ø16      | 1.578         |
| ø18      | 1.998         |
| ø20      | 2.466         |
| ø22      | 2.984         |
| ø25      | 3.853         |
| ø28      | 4.834         |
| ø32      | 6.313         |

## Next Steps

- [ ] Add Excel export
- [ ] Improve shape detection
- [ ] Add GUI interface
- [ ] Support block references
- [ ] Better diameter detection from line thickness
