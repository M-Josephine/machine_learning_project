#libraries

import streamlit as st
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

from PIL import Image
import requests
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.offsetbox import TextArea, DrawingArea, OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
from linkpreview import link_preview
from wordcloud import WordCloud

#title
st.title('Balance ton film')

#import of datasets
df = pd.read_csv('file:///C:/Users/jo_18/Desktop/FormationDATA/Projet_recommandation/links_movies.csv')
df2 = pd.read_csv('file:///C:/Users/jo_18/Desktop/FormationDATA/Projet_recommandation/userId_movieId_rating.csv',index_col=0)
tags_movies = pd.read_csv('file:///C:/Users/jo_18/Desktop/FormationDATA/Projet_recommandation/tags_movies.csv')

#modification of df
df['imdbId'] = df['imdbId'].astype(str)
df['imdbId'] = df['imdbId'].apply(lambda x: x.zfill(7))
df = df.drop(columns = 'Unnamed: 0')


#logo
image = Image.open('large_moviewatchers.png')

st.sidebar.image(image,
        use_column_width=True)



#wordcloud

def wordcloud(movie):
    if movie not in tags_movies['title'].tolist(): #some of the movies do not have tags, so we display an image instead saying 'Ihave no words'
        file_ = open("giphy3.gif", "rb")
        contents = file_.read()
        data_url = base64.b64encode(contents).decode("utf-8")
        file_.close()

        nowords = st.markdown(
        f'<img src="data:image/gif;base64,{data_url}" alt="cat gif">',
        unsafe_allow_html=True)
        return nowords
    else:    
        movie_Id = int(tags_movies[tags_movies['title'] == movie]['movieId'].unique())
        liste_tags= list(tags_movies[tags_movies['movieId'] == movie_Id]['tag'])
        
        text = str(liste_tags)
        text = text.replace("'","")
        
        fig, ax = plt.subplots(1,1,figsize = (4,2))
        ax1 = plt.subplot(111)
        
        wordcloud = WordCloud(width = 800, height= 400, background_color = 'white',max_words = 40,colormap = 'inferno').generate(text)
             
        ax1.imshow(wordcloud, interpolation="bilinear")
        ax1.axis("off")
        ax1.margins(x=0, y=0)
        
        return st.pyplot(fig) #the result is a figure
    
    
#recommender 1
def recommand_5(movie):

    neigh = NearestNeighbors(n_neighbors=6) #use of neirest neighbours algorithm, k=6 because we are looking for 5 closest neighbours (and itself)
    neigh.fit(df.iloc[:,4:24]) 
    input_movie = np.array(df[df['title']==movie])[:,4:24] 
    neigh.kneighbors(input_movie) 
                                    
    index_closest = list(neigh.kneighbors(input_movie)[1][0,0:]) 
    if df[df['title'] == movie].index.isin(index_closest): #we delete itself if it is included in th list
        index_closest.remove(df[df['title'] == movie].index) 
    else:
        index_closest = list(neigh.kneighbors(input_movie)[1][0,:5]) 
    liste_recommandations = list(df[df.index.isin(index_closest)].iloc[:,1]) 
    
    data={}

    for n in range(len(liste_recommandations)): #we create a dataframe with df2 to get the mean ratings of the selected movies
        movieid=str(df[df['title']== liste_recommandations[n]]['movieId'].tolist()[0])
        c_movieid=df2.columns.get_loc(movieid)

        title=liste_recommandations[n]
        nbrating=df2.iloc[:,c_movieid][df2.iloc[:,c_movieid]!=0].count()
        moyenne=df2.iloc[:,c_movieid][df2.iloc[:,c_movieid]!=0].mean()
        data[movieid]=title,nbrating,moyenne
        
    resultat=pd.DataFrame.from_dict(data, orient='index',columns=['title', 'nb_rating','moyenne'])#Conversion dictionnaire en df
     
    
    return resultat #the result is a dataframe



#recommender 2
def corr_rate5(movie):
    movieid=str(df[df['title']== movie]['movieId'].tolist()[0]) 

    #creation of a results dataframe
    data={} 
    _,c=df2.shape

    for n in range(c):
        title=df[df['movieId']==int(df2.columns[n])]['title'].unique().tolist()[0]
        correlation=df2.iloc[:,n].corr(df2[movieid]) #we calculate the correlations between the input movies and the others
        nbrating=df2.iloc[:,n][df2.iloc[:,n]!=0].count()
        moyenne=df2.iloc[:,n][df2.iloc[:,n]!=0].mean()
        data[df2.columns[n]]=title,correlation,nbrating,moyenne
        
    resultat=pd.DataFrame.from_dict(data, orient='index',columns=['title', 'corr', 'nb_rating','moyenne'])#Conversion dictionnaire en df

    resultat.drop([movieid],inplace=True)

    resultat = resultat.sort_values(by='corr',ascending=False).head()

    return resultat #the result is a dataframe


#input function
def input_sys_1():
    movie = st.selectbox(
    'Veuillez sélectionner un film que vous appréciez :',
     df['title'])
    
    return movie



#function to catch the url of the recommended movies
def catch_url(liste_movie):
    liste_url = []
    for i in liste_movie:
        imdbId = df[df['title'] == i]['imdbId']
        imdbId = imdbId.iloc[0]
        url_imbd = 'http://www.imdb.com/title/tt'+ imdbId +'/'
        liste_url.append(url_imbd)
    return liste_url


#function to scrap and display the posters of the 5 recommended movies and the mean rating / number of ratings
def get_display_image(liste_url,listenote,listenbnote):
    liste_image = []
    for url in liste_url:
        preview = link_preview(url)
        link_image = preview.image 
        response = requests.get(link_image) 
        image = Image.open(BytesIO(response.content)) 
        image = image.resize((170, 290), Image.ANTIALIAS) 
        liste_image.append(image)  #we scrap and create a list of the images
        
    fig, ax = plt.subplots(1,5,figsize = (25,6)) #creation of a figure 1x5
    for i in range(len(liste_image)):
        imagebox = OffsetImage(liste_image[i], zoom=1) #we place each image of the list in the figure
        ab = AnnotationBbox(imagebox, (0.5, 0.5))  
        ax[i].add_artist(ab)
        ax[i].axis('off') 
        
        Letitre="Note: "+str(round(listenote[i],1))+"/5 pour "+str(listenbnote[i])+" note(s)" #we create a title to insert in each subplot
        ax[i].set_title(Letitre,fontdict = {'fontsize': 13,'fontweight' : 'bold'})
        
    return st.pyplot(fig) #the result is a figure


#global function recommender 1
def recommandation_sys_1(movie):
    leresultat=recommand_5(movie)
    liste_movie = leresultat['title'].tolist()
    listenote=leresultat['moyenne'].tolist()
    listenbnote=leresultat['nb_rating'].tolist()
    liste_url = catch_url(liste_movie)
    liste_affiches = get_display_image(liste_url,listenote,listenbnote)
    return liste_affiches

#global function recommender 2
def recommandation_sys_2(movie):
    leresultat=corr_rate5(movie)
    liste_movie = leresultat['title'].tolist()
    listenote=leresultat['moyenne'].tolist()
    listenbnote=leresultat['nb_rating'].tolist()
    liste_url = catch_url(liste_movie)
    liste_affiches = get_display_image(liste_url,listenote,listenbnote)
    return liste_affiches

#input
movie = input_sys_1()

#wordcloud
st.header("Comment les utilisateurs définissent-ils ce film ?")
wordcloud(movie)


#recommender 1
st.header('Dans le même genre...')
recommandation_sys_1(movie)

#gif
file_ = open("giphy1.gif", "rb")
contents = file_.read()
data_url = base64.b64encode(contents).decode("utf-8")
file_.close()

st.markdown(
    f'<img src="data:image/gif;base64,{data_url}" alt="cat gif">',
    unsafe_allow_html=True,
)

#recommender 2
st.header('Les utilisateurs qui ont aimé ce film, ont aussi aimé...')
recommandation_sys_2(movie)


#stats viz
st.header('Quelques statistiques sur la base de données...')

#viz 1
image2 = Image.open('viz.png')

st.image(image2,
        use_column_width=True)
#viz 2
image3 = Image.open('viz2.png')

st.image(image3,
        use_column_width=True)
