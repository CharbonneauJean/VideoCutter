import os
import glob
import subprocess
import sys
import re
from shutil import move
from shutil import rmtree
from pytube import YouTube

if(os.path.isdir('TEMP')):
    rmtree('TEMP', ignore_errors=False)

currentVideoName = ''
chunkLength = 240 # in seconds
silentThreshold = 0.02
defaultFrameRate = float(30)

def get_valid_filename(s):
    s = str(s).strip().replace(' ', '_').replace(':', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)

def downloadFile(url):
    name = YouTube(url).streams.get_highest_resolution().download()
    realTitle = get_valid_filename(YouTube(url).title + ".mp4")
    os.rename(name,realTitle)
    return realTitle

def cutVideoInChunks(currentVidNumber):
    command = "ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 " + 'vid' + str(currentVidNumber) + '.mp4'
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    videoLength = float(result.stdout)
    
    if(chunkLength >= videoLength):
        return 1
    else:
        nbChunks = 0
        startPos = 0
        
        listFile = open('list.txt', 'w')

        while(startPos < int(videoLength)):
            nbChunks += 1
            command = "ffmpeg -i " + 'vid' + str(currentVidNumber) + '.mp4' + " -ss " + str(startPos) + " -t " + str(chunkLength) + " -c copy " + 'vid' + str(currentVidNumber) + "_" + str(nbChunks)  + '.mp4'
            subprocess.call(command, shell=True)
            command = "python jumpcutter.py --input_file " + 'vid' + str(currentVidNumber) + "_" + str(nbChunks)  + '.mp4' + " --output_file " + 'done_vid' + str(currentVidNumber) + "_" + str(nbChunks)  + '.mp4' + " --silent_speed 999999 --silent_threshold " + str(silentThreshold) + " --frame_rate " + str(defaultFrameRate)
            subprocess.call(command, shell=True)
            os.remove('vid' + str(currentVidNumber) + "_" + str(nbChunks)  + '.mp4')
            listFile.write("file '" + 'done_vid' + str(currentVidNumber) + "_" + str(nbChunks)  + '.mp4' + "'\n")
            startPos += chunkLength
        

        os.remove('vid' + str(currentVidNumber) + '.mp4')
        listFile.close()

        command = 'ffmpeg -f concat -safe 0 -i list.txt -c copy ' + currentVideoName
        print(command)
        subprocess.call(command, shell=True)

        os.remove('list.txt')

        fileList = glob.glob('done*')

        for filePath in fileList:
            try:
                os.remove(filePath)
            except:
                print("Error while deleting file : ", filePath)
        

        return nbChunks

videoListFile = open('tocut.txt')

youtubeUrls = videoListFile.readlines()

count = 1

for youtubeVideoUrl in youtubeUrls: 
    if("youtube.com" in youtubeVideoUrl):
        currentVideoName = downloadFile(youtubeVideoUrl.strip())
    else:
        thisVideoName = youtubeVideoUrl.strip()
        currentVideoName = get_valid_filename(thisVideoName)
        os.rename(thisVideoName,currentVideoName)
    newName = 'vid' + str(count) + '.mp4'
    os.rename(currentVideoName, newName)

    # Calcul du framerate de la vidéo pour éviter les desynchronisations
    command = "ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate -of default=noprint_wrappers=1:nokey=1 " + newName
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout)
    framerateString = str(result.stdout)[2:-5]
    print(framerateString)
    if("60/1" in framerateString):
        defaultFrameRate = float(60)
    else:
        a = int(framerateString.split('/')[0])
        b = int(framerateString.split('/')[1])
        defaultFrameRate = float(a/b)
    
    nbChunks = cutVideoInChunks(count)

    if(nbChunks == 1):
        command = "python jumpcutter.py --input_file " + newName + " --output_file " + currentVideoName + " --silent_speed 999999 --silent_threshold " + str(silentThreshold) + " --frame_rate " + str(defaultFrameRate)
        subprocess.call(command, shell=True)
        os.remove(newName)

    count+=1

