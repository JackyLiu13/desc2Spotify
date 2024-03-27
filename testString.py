
import re 
def convert_song_names(description):
    pattern = r'\s*\d{2}:\d{2} '
    return [tuple(re.split(pattern, line.strip())[1].split(' - ')) for line in description.split('\n') if re.match(pattern, line)]

  
descriptionSongs = """
"""
songs = convert_song_names(descriptionSongs)
print(songs)
