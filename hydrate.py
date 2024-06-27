import tweepy
import json
import gzip
from pathlib import Path
from tqdm import tqdm

# Credențialele API Twitter
consumer_key = "K3iEN9DTedSFkug8md8X79dUW"
consumer_secret = "JKaNhLo5Ar8AdF6l7k8nVqRgttTREAaYyAAwzPIbmJbzUswoEo"
access_token = "1799009466727456768-aRCfvwAQZiM8dWdNcE0bawwKuW32Us"
access_token_secret = "4TFdDinTbQ8sxcFRKNij57LKUh3d3YNyATyiiOEjBLHTd"

# Funcție pentru verificarea autentificării și returnarea obiectului API
def get_api():
   auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
   api = tweepy.Client(auth)
   return api

# Obținerea obiectului API
api = get_api()

# Funcție pentru citirea în blocuri a fișierului
def _reader_generator(reader):
   b = reader(1024 * 1024)
   while b:
       yield b
       b = reader(1024 * 1024)

# Funcție pentru numărarea liniilor din fișier
def raw_newline_count(fname):
   f = open(fname, 'rb')
   f_gen = _reader_generator(f.raw.read)
   return sum(buf.count(b'\n') for buf in f_gen)

# Funcție pentru împărțirea listei în bucăți
def chunkify(lst, n):
   for i in range(0, len(lst), n):
       yield lst[i:i + n]

# Funcție pentru hidratarea fișierului cu ID-uri
def hydrate(id_file):
   print(f'Hidratare {id_file}')

   gzip_path = id_file.with_suffix('.jsonl.gz')
   if gzip_path.is_file():
       print(f'Salt fișier JSON, există deja: {gzip_path}')
       return

   num_ids = raw_newline_count(id_file)

   tweet_ids = []
   with id_file.open() as f:
       for line in f:
           tweet_ids.append(line.strip())

   with gzip.open(gzip_path, 'wt', encoding='utf-8') as output:
       with tqdm(total=num_ids) as pbar:
           for chunk in chunkify(tweet_ids, 100):  # împărțim în bucăți de câte 100 ID-uri
               try:
                   tweets = api.get_tweets(ids=chunk, tweet_fields=["id", "created_at", "text"], expansions=["author_id"], user_fields=["id", "name", "username"])
                   for tweet in tweets.data:
                       output.write(json.dumps(tweet) + "\n")
               except tweepy.TweepyException as e:
                   print(f"Eroare la hidratarea tweet-urilor: {e}")
                   continue
               except Exception as ex:
                   print(f"O eroare neașteptată a apărut: {ex}")
                   continue

               pbar.update(len(chunk))

# Funcția principală
def main():
   data_dirs = ['2023-02']

   for data_dir in data_dirs:
       if not Path(data_dir).exists():
           raise Exception(f"Directorul nu există: {data_dir}")
       for path in Path(data_dir).iterdir():
           if path.name.endswith('.txt'):
               print(f"Procesare fișier: {path}")
               hydrate(path)

if __name__ == "__main__":
   main()
