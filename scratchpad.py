import pandas as pd
user_email='aadi2000@uw.edu'
df=pd.read_csv("data/spotify_emails_responses.csv")
print(int(df[df['email']==user_email]['split']))