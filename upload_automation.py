import os
import random
import subprocess
from pathlib import Path
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload

scopes = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl", "https://www.googleapis.com/auth/youtube" ]

# Metadata inputs
motivational_keywords = [
    "motivation", "success", "mindset", "inspiration", "discipline", "growth", 
    "positive vibes", "mental toughness", "nevergiveup", "dreambig", "selfimprovement", "dailyinspiration"
]
popular_hashtags = [
    "MotivationMonday", "InspirationDaily", "SuccessMindset", "KeepGoing", 
    "BelieveInYourself", "StayPositive", "HustleHard"
]
titles = [
    "Unlock Your Full Potential 🔥",
    "Start Your Day with Motivation 💪",
    "One Quote That Will Change Your Life 🌟",
    "Discipline is the Bridge to Success 💯",
    "Your Mindset Shapes Your Reality 🌍"
]
descriptions = [
    "Watch this powerful motivational quote that will ignite your inner fire and push you closer to your goals.",
    "Start your day right with this inspiring quote. Perfect for morning motivation!",
    "Need a boost of motivation? This quote will lift your spirits and keep you focused.",
    "Stay disciplined. Stay focused. Let this quote remind you of your true potential.",
    "Inspiration is fuel for the soul. Let this quote empower your journey today."
]

def generate_video_metadata():
    title = random.choice(titles)
    description = random.choice(descriptions)
    random.shuffle(motivational_keywords)
    random.shuffle(popular_hashtags)
    tags = random.sample(motivational_keywords, 5) + random.sample(popular_hashtags, 3)
    hashtags = " ".join([f"#{tag.replace(' ', '')}" for tag in tags])
    full_description = f"{description}\n\n{hashtags}"
    return title, full_description, tags


def add_watermark(input_video, watermark_image, output_video, position="10:10"):
    command = [
        "ffmpeg", "-y", "-i", input_video, "-i", watermark_image,
        "-filter_complex",
        "[1:v]scale=400:-1[wm];[0:v][wm]overlay=10:main_h-overlay_h-10",
        output_video
    ]
    subprocess.run(command, check=True)



def generate_thumbnail(input_video, thumbnail_output, time="00:00:05"):
    command = [
        "ffmpeg", "-y", "-ss", time, "-i", input_video,
        "-vframes", "1", thumbnail_output
    ]
    subprocess.run(command, check=True)

def load_uploaded_files(tracker_file="uploaded_videos.txt"):
    if os.path.exists(tracker_file):
        with open(tracker_file, "r") as f:
            return set(line.strip() for line in f)
    return set()

def save_uploaded_file(file_name, tracker_file="uploaded_videos.txt"):
    with open(tracker_file, "a") as f:
        f.write(file_name + "\n")

def upload_video(youtube, input_file):
    base_name = Path(input_file).stem
    watermarked_video = f"output/{base_name}_wm.mp4"
    thumbnail = f"output/{base_name}_thumb.jpg"
    watermark_image = "nktech.png"
    playlist_id = "PLxFWU3M8Ur0wLUmAuoCvKzMtmAKS1VuKV"  # Optional

    print(f"Processing: {input_file}")
    os.makedirs("output", exist_ok=True)

    # Add watermark and generate thumbnail
    add_watermark(input_file, watermark_image, watermarked_video)
    generate_thumbnail(watermarked_video, thumbnail)

    title, description, tags = generate_video_metadata()
    keywords_line = ", ".join(tags)
    full_description = f"{description}\n\nKeywords: {keywords_line}"

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": full_description,
                "tags": tags,
                "categoryId": "22",
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en"
            },
            "status": {
                "privacyStatus": "public",
                "publicStatsViewable": True,
                "selfDeclaredMadeForKids": False,
                "madeForKids": False,
                "license": "creativeCommon",
                "embeddable": True
            }
        },
        media_body=MediaFileUpload(watermarked_video)
    )
    response = request.execute()
    video_id = response["id"]
    print(f"Uploaded: {base_name} ✅ | Video ID: {video_id}")

    # Set thumbnail
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(thumbnail)
    ).execute()

    # Add to playlist
    if playlist_id:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()
        print(f"📺 Added to playlist: {playlist_id}")

    # Post a comment
    youtube.commentThreads().insert(
        part="snippet",
        body={
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": "🔥 What did you think about this quote? Drop your thoughts below!"
                    }
                }
            }
        }
    ).execute()

    # ✅ Delete original file after upload
    try:
        os.remove(input_file)
        os.remove(watermarked_video)
        os.remove(thumbnail)

        print(f"🗑️ Deleted original file: {input_file}")
    except Exception as e:
        print(f"⚠️ Could not delete file: {e}")

    return base_name

def main():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "testGoogle2.json"

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_local_server(port=0)
    youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

    uploaded = load_uploaded_files()
    video_folder = "videos"

    for file in sorted(os.listdir(video_folder)):
        if not file.lower().endswith(('.mp4', '.mov', '.avi')):
            continue

        full_path = os.path.join(video_folder, file)
        file_base = Path(file).stem

        if file_base in uploaded:
            continue

        try:
            uploaded_name = upload_video(youtube, full_path)
            save_uploaded_file(uploaded_name)
            break  # ✅ Stop after uploading one video
        except Exception as e:
            print(f"❌ Error uploading {file}: {e}")
            break  # Stop here, don’t try next video today




if __name__ == "__main__":
    main()