from src.transformation import read_from_postgres, Transformation, Aggregation
from src.notification import smtp_send_email, discord_webhook
import logging
import os
from dotenv import load_dotenv
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/transformation_and_notifications.log', mode = 'w'),
        logging.StreamHandler()
    ],
    force=True
)

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

AGG_DIR = "data/aggregation"
DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': 'postgres_docker',
    'port': 5432}

SMTP_CONFIG = {
    'sender_email': os.getenv('SMTP_USER'),
    'sender_password': os.getenv('SMTP_PASSWORD'),
    'recipient_email': os.getenv('EMAIL_TO'),
    'subject': 'Shieran Juvi Purwadhika Capstone 1 JCDEAH007',
    'body': """Halo Kak,

Berikut saya lampirkan hasil agregasi data dari Yellow & Green Taxi bulan Januari 2025.
Seluruh data telah melalui proses transformasi, berupa pembersihan nama kolom dan baris data. 
Hasil agregasi meliputi:

1. Kinerja Vendor – Rata-rata tarif, total jarak tempuh, dan jumlah perjalanan per vendor.
2. Analisis Pendapatan per Vendor – Total tarif, total tip, dan total pendapatan keseluruhan.
3. Statistik Tip per Vendor – Nilai tip minimum, maksimum, dan total tip per vendor.
4. Jumlah Perjalanan Berdasarkan Hari dan Vendor – Jumlah perjalanan per run_id dan vendor.
5. Distribusi Pembayaran – Jumlah perjalanan, rata-rata tarif, rata-rata tip, total pendapatan, dan persentase distribusi per metode pembayaran.

Hasil agregasi berupa file .csv telah saya attach pada email ini.
Berikut link gdrive yang saya gunakan untuk mengupload dokumentasi: https://drive.google.com/drive/folders/16satXN4gXfUQvdOytjUIURU6iTSXjL2O?usp=sharing
Terima kasih atas perhatiannya.
        """,
    'folder_path': AGG_DIR
    #'keyword': "yellow" optional
}

DISCORD_CONFIG = {
    "personal": {
    "discord_webhook_url": os.getenv('DISCORD_WEBHOOK_URL_PERSONAL'),
    "content" :"""
   Testing Discord Webhook! 
1. Kinerja Vendor – Rata-rata tarif, total jarak tempuh, dan jumlah perjalanan per vendor.
2. Analisis Pendapatan per Vendor – Total tarif, total tip, dan total pendapatan keseluruhan.
3. Statistik Tip per Vendor – Nilai tip minimum, maksimum, dan total tip per vendor.
4. Jumlah Perjalanan Berdasarkan Hari dan Vendor – Jumlah perjalanan per run_id dan vendor.
5. Distribusi Pembayaran – Jumlah perjalanan, rata-rata tarif, rata-rata tip, total pendapatan, dan persentase distribusi per metode pembayaran.

Terima kasih atas perhatiannya.
    """,
    "username" : "Shieran"
    },
    
    "capstone1": {
    "discord_webhook_url": os.getenv('DISCORD_WEBHOOK_URL_CAPSTONE'),
    "content" :"""

Berikut penggunaan discord webhook dan ringkasan agregasi data dari Green & Yellow Taxi bulan Januari 2025.
Seluruh data telah melalui proses transformasi, berupa pembersihan nama kolom dan baris data. Hasil agregasi meliputi:

1. Kinerja Vendor – Rata-rata tarif, total jarak tempuh, dan jumlah perjalanan per vendor.
2. Analisis Pendapatan per Vendor – Total tarif, total tip, dan total pendapatan keseluruhan.
3. Statistik Tip per Vendor – Nilai tip minimum, maksimum, dan total tip per vendor.
4. Jumlah Perjalanan Berdasarkan Hari dan Vendor – Jumlah perjalanan per run_id dan vendor.
5. Distribusi Pembayaran – Jumlah perjalanan, rata-rata tarif, rata-rata tip, total pendapatan, dan persentase distribusi per metode pembayaran.

Terima kasih atas perhatiannya.
    """,
    "username" : "Shieran"
    }
}

def main(): 
    logging.info("="*80)
    logging.info("Transformation & Notification Starting...")
    logging.info("="*80)

    try:
        logging.info("Reading from Postgres")
        final_combined = read_from_postgres(**DB_CONFIG)
        
        if not final_combined:
            logging.error("Failed to connect to Postgres")
            raise

        logging.info("Transforming data...")
        transformation = Transformation(final_combined)
        transformed_data = transformation.transform()

        logging.info("Starting Aggregation...")
        aggregation = Aggregation(transformed_data)
        all_aggs = aggregation.aggregations_to_csv()

        #email smtp
        logging.info("SMTP starting...")
        smtp_send_email(**SMTP_CONFIG)

        #send notification DISCORD
        logging.info("Sending to Discord...")
        for url, content in DISCORD_CONFIG.items():
            discord_webhook(**content)
            logging.info(f"Webhook send to {url}")
    except Exception as e:
        logging.error(f"Transformation & Notification fails due to {e}")

if __name__ == "__main__":
    main()

