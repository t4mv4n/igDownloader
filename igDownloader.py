import configparser
import json
import re
import os
import requests
import shutil
import time

def DownloadIDs():
    config = configparser.ConfigParser()
    config.read('id.config')
    idList = config.get("IG", "ID").split(",")
    return idList

def GetImageURLs( igID):
    imageURLs = []
    contents = requests.get('https://www.instagram.com/' + igID, stream=True).text
    lines = contents.split("\n")
    del contents
    
    cnt = 0
    for line in lines:
        if ">window._sharedData" in line:
            first = line.index("{")
            last = len(line) - line[::-1].index("}")
            jsonString = line[first:last]
            jObj = json.loads(jsonString)
            temp = jObj['entry_data']
            profile = temp['ProfilePage']
            edges = profile[0]['graphql']['user']['edge_owner_to_timeline_media']['edges']
            for edge in edges:
                node = edge['node']
                __typename = node['__typename']
                shortcode = node['shortcode']
                isVideo = node['is_video']
                display_url = node['display_url']
                if isVideo:
                    postURL = 'https://www.instagram.com/p/'  + shortcode + '/?taken-by=' + igID
                    try:
                        postContent = requests.get(postURL, stream=True).text
                        postLines = postContent.split("\n")
                    except (http.client.IncompleteRead) as e:
                        print('Cannot read post: ' + postURL)
                    del postContent
                    imageURLs.extend(GetImageLinks(postLines))
                else:
                    imageURLs.append(display_url)
                
            break
    return imageURLs

    
    
def GetImageLinks( postLines):
    urlList = []
    for postLine in postLines:
        matchObj = ''
        if '<meta property="og:image"' in postLine and'/vp/' in postLine:
            matchObj = re.search('https://[a-zA-Z0-9/\._\-]*\.jpg',postLine)
        elif '_n.mp4"' in postLine:
            matchObj = re.search('https://[a-zA-Z0-9/\._\-]*\.mp4',postLine)
        if matchObj:
           url = matchObj.group(0)
           #print(url)
           if(url not in urlList):
               urlList.append(url)
    return urlList
   
def CreateFolder( directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def GenImageName( url):
    return url[len(url) - url[::-1].index("_",10):]

def DownloadImage( url, fileName):
    if not os.path.isfile(fileName):
        response = requests.get(url, stream=True)
        if response.status_code == requests.codes.ok:
            with open(fileName, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
                print("   Downloaded: " + fileName)
        del response
        
def StartDownload(downloadID):
    downloadPath = "Images/" + downloadID
    CreateFolder(downloadPath)
    print('Checking ID: ' + downloadID + '...')
    urls = GetImageURLs(downloadID)
    for imageURL in urls:        
        DownloadImage(imageURL, downloadPath + "/" + GenImageName(imageURL))
        
idList = DownloadIDs()
for downloadID in idList:
    StartDownload(downloadID)
