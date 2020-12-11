import os
import requests
import eyed3
from tabulate import tabulate

print('\n','-'*19,'AUTOMETADATA','-'*19,'\n')

location = input('[Enter location / name of music file(s) (Leave blank if current directory)] ') + '/'

# if blank
if location.strip() == '' : location = os.getcwd()

# if folder
if os.path.isdir(location): files = [file for file in os.listdir(location) if file.endswith(('mp3','wav','aiff','aac','wma','m4a'))] 

# if file
elif os.path.isfile(location): files = [location]

# if neither a file nor a folder 
else:
    print('INVALID. Please check again.')
    exit()

print('\n','-'*50,'\n')


def convert_file_name_to_searchable_term(file):
    file = file.lower()

    #remove the extension
    index_of_last_dot = file.rfind('.')
    file = file[:index_of_last_dot]

    #remove Unwanted info
    unwanted_info_list = ['official','unofficial','video','audio','lyric','lyrics','(',')','-']
    
    for unwanted_info in unwanted_info_list:
        if unwanted_info in file:
            file = file.replace(unwanted_info,'')
    
    return file.strip()

with open('api_key') as f:
    api_key = f.readline()
     
def search_genius(search_term):
    url = f'https://api.genius.com/search?q={search_term}&page=1&per_page=3&access_token={api_key}'

    response = requests.get(url)

    if response :
        return response.json()
    else :
        print('An error occured for getting result from genius')
        exit()


def get_metadata_from_response(response):
    hits = response['response']['hits']
    num_of_hits = len(hits)

    song_title_list = []
    artist_list = []
    album_art_list = []

    for i in range(num_of_hits):
        song_title_list.append(hits[i]['result']['title_with_featured'])
        artist_list.append(hits[i]['result']['primary_artist']['name'])
        album_art_list.append(hits[i]['result']['song_art_image_url'])

    return [song_title_list , artist_list , album_art_list]


def apply_metadata(file_name):
    print('Applying Metadata for',file_name)

    #apply song title
    audio_file.tag.title = song_title
    print('- Applied Title -',song_title)

    #apply artist name
    audio_file.tag.artist = artist
    print('- Applied Artist Name -',artist)

    #apply album name
    audio_file.tag.album = artist #done just so album art displays correctly on mobile

    #apply album art if it is not '-' (which is kept when metadata is not received from genius even after implicit search)
    if album_art != '-':
        image = requests.get(album_art)

        with open('album_art.jpg','wb') as img_file:
            img_file.write(image.content)

        audio_file.tag.images.set(3, open('album_art.jpg','rb').read(), 'image/jpeg')
        os.remove('album_art.jpg')

        print('- Applied Album Art')


# makes the file name artist + song name
def change_file_name():
    index_of_last_dot = path_to_file.rfind('.')
    extension = path_to_file[index_of_last_dot:]

    os.rename(path_to_file,f'{location}/{artist} - {song_title}{extension} ')
    print('- Changed file name')


metadata = { 'available': [] , 'in_use': [] }

files_without_metadata_received = []
files_without_proper_metadata_shown = []

# Searches genius for metadata based on file name
# Adds it to the dict metadata as available (complete metadata received) and as in_use (the first hits of metadata received)
for i in range(len(files)):
    file = files[i]
    print(f'[{i+1}/{len(files)}] {file}')
    
    # searches and gets the response from genius
    search_term = convert_file_name_to_searchable_term(file)
    genius_response = search_genius(search_term)

    # decodes the response into lists of song_title artist , and album art
    song_title_list , artist_list , album_art_list = get_metadata_from_response(genius_response)

    # adds all metadata to available key of metadata
    metadata['available'].extend([[file,song_title_list,artist_list,album_art_list]])

    if len(song_title_list) == 0 :
        files_without_metadata_received.append(file) # This list is mode so that in the end we can ask input for implicit search
        song_title_list.append('-')
        artist_list.append('-')
        album_art_list.append('-')
         

    # adds only the 1st metadata of each song to in_use key of metadata
    metadata['in_use'].extend([[ #remove i+1
        file,
        song_title_list[0],
        artist_list[0],
        album_art_list[0]
    ]])
     
    

# displays the table for confirmation
print('\n',tabulate(
        [metadata['in_use'][i][:-1] for i in range(len(metadata['in_use']))],
        headers=['ID','File name','Song Title','Artist'],
        showindex=True
    ))


ids_of_wrong_metadata = list(map(int,input('\n[Enter ID of music files with wrong metadata (eg: \' 0 3 15 \' ) (Leave blank if none) (Ignore ones with - in columns) ] ').split()))

ids_of_wrong_metadata_in_range = []
ids_of_wrong_metadata_out_of_range = []

for id in ids_of_wrong_metadata:
    if id-1 < len(files) :
        ids_of_wrong_metadata_in_range.append(id)
    else:
        ids_of_wrong_metadata_out_of_range.append(id)

# gets the file names of those without proper metadata using index from ids_of_wrong_metadata_in_range
files_without_proper_metadata_shown = [ [i,metadata['available'][i]] for i in ids_of_wrong_metadata_in_range ]

# For checking if other metadata responses is correct
for file_info in files_without_proper_metadata_shown:
    index_of_file = file_info[0] 
    file = file_info[1][0]
    
    for i in range(1,len(metadata['available'][index_of_file][1])): # starts from the 2nd result because first one was displayed

        song_title = metadata['available'][index_of_file][1][i]
        artist = metadata['available'][index_of_file][2][i]
        album_art = metadata['available'][index_of_file][3][i]

        print(f'\nIs {file} : \n- {song_title}\n- by {artist}')

        is_correct = input('[y / n] ') in ('y','')
        
        print()

        if is_correct:
            print('-'*50)
            metadata['in_use'][index_of_file] = [file,song_title,artist,album_art]
            break

    else:
        # Adds it to list of files without metadata since none of the 3 received was correct
        # doesnt add if this is one without metadata from the start
        if file not in files_without_metadata_received : 
            files_without_metadata_received.append(file)


# removes info of files for which metadata was not received
for file in files_without_metadata_received:
    for i in metadata['in_use']:
        if file in i :
            metadata['in_use'].remove(i)


# Asks implicitly for song title and artist name, then searches genius
for file in files_without_metadata_received:
    print(f'\nFor {file} , What is the ')
    
    song_title_input = input('[Song Title] ')
    artist_input = input('[Artist] ')

    search_term = f'{song_title_input} {artist_input}'

    # searches and gets the response from genius
    search_term = convert_file_name_to_searchable_term(search_term)
    genius_response = search_genius(search_term)

    # decodes the response into lists of song_title artist , and album art
    song_title_list , artist_list , album_art_list = get_metadata_from_response(genius_response)
    
    for i in range(len(song_title_list)):
        song_title = song_title_list[i]
        artist = artist_list[i]
        album_art = album_art_list[i]

        print(f'\nIs {file} : \n- {song_title}\n- by {artist}')
        is_correct = input('[y / n] ') in ('y','')
        print()
        
        if is_correct: 
            break

    else:
        # If none of these were correct 
        print("Could not find proper metadata for this. Will be applying only title and artist.")
        song_title = song_title_input.title()
        artist = artist_input.title()
        album_art = '-'
    
    metadata['in_use'].append([file,song_title,artist,album_art])

print('-'*50)

# applying the metadata to files

for file_info in metadata['in_use']:
    # get the audio file
    path_to_file = f'{location}/{file_info[0]}'
    audio_file = eyed3.load(path_to_file)

    # Get the required metadata from list
    song_title = file_info[1]
    artist = file_info[2]
    album_art = file_info[3]

    apply_metadata(file_info[0])

    audio_file.tag.save(version=eyed3.id3.ID3_V2_3)
    change_file_name() 

    print()

print('-'*19,'END','-'*19)