Inside the folder mobile-ios-pwa, read every file and folder and understand the project structure. After that, make a plan to add a new function to the app. The new function is a carb calculator through pictures. The user will upload a picture of a food or dish and the app will calculate the carbs in it. The app should use the existing backend to calculate the carbs. 

Also I want you to follow my professor's instructions. 

oi! O dataset que tem os pratos com volume e calorias esta abaixo, o
read.me produzido pelo meu treinamento. O download tem de ser feito a
mao, no meu caso. O prompt que usei foi:

I want to obtain several pictures of dishes. For each dish, I want to
have the amount of calories. With this set, I want to train a neural
network so that, given a photo of a dish, I can predict the amount of
calories. The training must take into account the color and relative
volume of different food, so that we can increase the precision on the
forecast.

que pode OBVIAMENTE ser melhorado (deveria :-)). Mas isto pode esperar
tu pegares uma cor na praia, nao exagera.

Bom final de semana

Luigi

# Calorie Estimator

This project uses Deep Learning to estimate the number of calories in
a dish from a photo.

## Setup

1. Run `setup_env.bat` to create a virtual environment and install dependencies.
2. Activate the environment: `.venv\Scripts\activate`

## Usage

### Training used Mock Data (for testing pipeline)

```bash
python src/train.py --mock --epochs 2
```

### Training with Real Data

1. Download the **Nutrition5k** dataset.
2. Organize it into `data/raw`.
3. Update `src/data_loader.py` to correctly parse the dataset metadata
(CSV files).
4. Run:

    ```bash
    python src/train.py --data_dir data/raw
    ```

### Inference

```bash
python src/predict.py --image_path path/to/your/image.jpg
```