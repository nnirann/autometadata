import os
import requests
import eyed3

print('\n','-'*19,'AUTOMETADATA','-'*19,'\n')

location = input('[Enter location / name of music file(s) (Leave blank if current directory)] ')

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


try:
    download_method = int(input('Choose download method -\n\
[1] Fully automatically (won\'t be that accurate) \n\
[2] Only ask if there is trouble finding the song \n\
[3] Ask for confirmation on every song \n\
: '))

# if no input given
except ValueError:
    print('Not a valid answer. Please try again.')
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


def get_metadata_from_shazam():
    responses = shazam_response['response']['hits']
    num_of_responses = len(responses)

    song_title_list = []
    artist_list = []
    album_art_list = []

    for i in range(num_of_responses):
        song_title_list.append(responses[i]['result']['title_with_featured'])
        artist_list.append(responses[i]['result']['primary_artist']['name'])
        album_art_list.append(responses[i]['result']['song_art_image_url'])

    return [song_title_list , artist_list , album_art_list]


def apply_metadata():
    #apply song title
    audio_file.tag.title = song_title
    print('- Applied Title -',song_title)

    #apply artist name
    audio_file.tag.artist = artist
    print('- Applied Artist Name -',artist)

    #apply album name
    audio_file.tag.album = artist #done just so album art displays correctly on mobile

    #apply album art
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


def ask_for_name_of_song_and_artist():
    name = input('[Song Name] ')
    artist = input('[Artist Name] ')
    print()
    return [name,artist]


for index,file in enumerate(files):
    print('\n','-'*50,'\n')

    print(f'[{index + 1}] {file}\n')

    file_name = convert_file_name_to_searchable_term(file)

    shazam_response = search_genius(file_name)

    was_shazam_searched_with_explicit_name = False

    index_of_response_used = 0

    while True:
        try:
            # so that it asks user for song title and artist
            if index_of_response_used == 3: raise KeyError()

            song_title_list , artist_list , album_art_list = get_metadata_from_shazam()

            if len(song_title_list) == 0 : raise KeyError() # no result

            if download_method == 3:
                is_it_correct_response = input(f'[Is this {song_title_list[index_of_response_used]} by {artist_list[index_of_response_used]} ? ( y / n ) ] ') in ('y','')

                if not is_it_correct_response : 
                    index_of_response_used += 1 
                    continue

            
            # get the audio file
            path_to_file = f'{location}/{file}'
            audio_file = eyed3.load(path_to_file)

            # Get the required metadata from list
            song_title = song_title_list[index_of_response_used]
            artist = artist_list[index_of_response_used]
            album_art = album_art_list[index_of_response_used]

            apply_metadata()
            
            audio_file.tag.save(version=eyed3.id3.ID3_V2_3)
            change_file_name() 
        
            print('\n','-'*50,'\n')

            break

        # arises when Shazam doesnt give adequate info
        except (KeyError , TypeError): 
            print('\nWe were unable to find result for',file)
            
            if not was_shazam_searched_with_explicit_name and download_method != 1:
                print('Please give the name of song and artist for further checking. (Leave blank if you are not sure.)\n')
                
                song_name_input_given , artist_input_given = ask_for_name_of_song_and_artist()

                new_search_term = f'{song_name_input_given} {artist_input_given}'
                shazam_response = search_genius(new_search_term)
                
                was_shazam_searched_with_explicit_name = True

                index_of_response_used = 0

                continue # makes it try getting response from shazam 
            
            print('\n','-'*50,'\n')   

            index_of_response_used = 0
            break

        except Exception as err:
            print('An error occured -',err)
            print(file,'skipped.')

            break