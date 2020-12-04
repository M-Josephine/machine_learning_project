import streamlit as st
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

#import des librairies fonction get_display_image
from PIL import Image
import requests
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.offsetbox import TextArea, DrawingArea, OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
from linkpreview import link_preview
#import tkinter
#import matplotlib
#matplotlib.use('TkAgg')
import base64

st.title('Balance ton film')

#import du df movies avec les dummies + links
df = pd.read_csv('file:///C:/Users/jo_18/Desktop/FormationDATA/Projet_recommandation/links_movies.csv')

df2 = pd.read_csv('file:///C:/Users/jo_18/Desktop/FormationDATA/Projet_recommandation/userId_movieId_rating.csv',index_col=0)

#modification de la colonne imdbId
df['imdbId'] = df['imdbId'].astype(str)
df['imdbId'] = df['imdbId'].apply(lambda x: x.zfill(7))

#on drop la colonne de l'ancien index
df = df.drop(columns = 'Unnamed: 0')


#logo
image = Image.open('large_moviewatchers.png')

st.sidebar.image(image,
        use_column_width=True)



#wordcloud
from wordcloud import WordCloud

tags_movies = pd.read_csv('file:///C:/Users/jo_18/Desktop/FormationDATA/Projet_recommandation/tags_movies.csv')

def wordcloud(movie):
    if movie not in tags_movies['title'].tolist():
        #nowords = print('No tags found')
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
        
        return st.pyplot(fig)
    
    
#fonction de recommandation 1
def recommand_5(movie):

    neigh = NearestNeighbors(n_neighbors=6) # on cherche les 5 plus proches voisins (5+lui-meme donc n_neighbors=6)
    neigh.fit(df.iloc[:,4:24]) #on prend les colonnes binaires correspondants aux genres
    input_movie = np.array(df[df['title']==movie])[:,4:24] #on cree un array a partir du film donné en input
    neigh.kneighbors(input_movie) #on applique la fonction kneighbors pour trouver les 5 plus proches. Elle nous ressort un array
                                    #avec les distances et un array avec les 5 plus proches + lui-meme
    index_closest = list(neigh.kneighbors(input_movie)[1][0,0:]) #on cree une liste d'index avec les 6 plus proches (dont lui-meme) à partir de l'array
    if df[df['title'] == movie].index.isin(index_closest):
        index_closest.remove(df[df['title'] == movie].index) #on supprime l'index qui correspond a lui meme s'il est dans la liste
    else:
        index_closest = list(neigh.kneighbors(input_movie)[1][0,:5]) #sinon, on sélectionne les 5 premiers index de la liste
    liste_recommandations = list(df[df.index.isin(index_closest)].iloc[:,1]) #on va chercher les titre de films correspondants aux 5 index restants
    
    data={}

    for n in range(len(liste_recommandations)):
        movieid=str(df[df['title']== liste_recommandations[n]]['movieId'].tolist()[0])
        c_movieid=df2.columns.get_loc(movieid)

        #data[movieId]=title,correlation, nb rating ,mean
        title=liste_recommandations[n]
        nbrating=df2.iloc[:,c_movieid][df2.iloc[:,c_movieid]!=0].count()
        moyenne=df2.iloc[:,c_movieid][df2.iloc[:,c_movieid]!=0].mean()
        data[movieid]=title,nbrating,moyenne
        
    resultat=pd.DataFrame.from_dict(data, orient='index',columns=['title', 'nb_rating','moyenne'])#Conversion dictionnaire en df
     
    
    return resultat



#fonction de recommandation corrélation
def corr_rate5(movie):
    movieid=str(df[df['title']== movie]['movieId'].tolist()[0]) #movieId de Toys Story est 1
    #df2 = pd.read_csv('file:///C:/Users/jo_18/Desktop/FormationDATA/Projet_recommandation/userId_movieId_rating.csv',index_col=0)

    #Création d'un df resultat avec en index movieId, colonnes(titre, correlation avec le film choisi,nombre de notes)
    data={} 
    _,c=df2.shape#recuperation du nombre de colonnes pour la boucle

    for n in range(c):
        #data[movieId]=title,correlation, nb rating ,mean
        title=df[df['movieId']==int(df2.columns[n])]['title'].unique().tolist()[0]
        correlation=df2.iloc[:,n].corr(df2[movieid])
        nbrating=df2.iloc[:,n][df2.iloc[:,n]!=0].count()
        moyenne=df2.iloc[:,n][df2.iloc[:,n]!=0].mean()
        data[df2.columns[n]]=title,correlation,nbrating,moyenne
        
    resultat=pd.DataFrame.from_dict(data, orient='index',columns=['title', 'corr', 'nb_rating','moyenne'])#Conversion dictionnaire en df

    resultat.drop([movieid],inplace=True)#On sort le film choisi du dataframe

    resultat = resultat.sort_values(by='corr',ascending=False).head()

    return resultat


#fonction input
def input_sys_1():
    #movie = st.text_input('Veuillez saisir un film que vous avez déjà vu et aimé : ')
    #movie = str(input('Veuillez saisir un film que vous avez déjà vu et aimé : '))
    movie = st.selectbox(
    'Veuillez sélectionner un film que vous appréciez :',
     df['title'])
    
    return movie



#fonction pour recuperer la liste des url des films recommandes
def catch_url(liste_movie):
    liste_url = []
    for i in liste_movie:
        imdbId = df[df['title'] == i]['imdbId']
        imdbId = imdbId.iloc[0]
        url_imbd = 'http://www.imdb.com/title/tt'+ imdbId +'/'
        liste_url.append(url_imbd)
    return liste_url


#fonction pour afficher les affiches des 5 films recommandés dans une figure matplotlib


def get_display_image(liste_url,listenote,listenbnote):
    liste_image = []
    for url in liste_url:
        preview = link_preview(url)
        link_image = preview.image #on crée le lien de l'image
        response = requests.get(link_image) #on récupère le lien de l'image
        image = Image.open(BytesIO(response.content)) #on ouvre l'image en tant que fichier à partir de son lien (on la transforme en fichier binaire)
        image = image.resize((170, 290), Image.ANTIALIAS) #on ajuste la taille de l'image
        liste_image.append(image)  #on cree une liste avec les objects images des 5 affiches

    fig, ax = plt.subplots(1,5,figsize = (25,6)) #on crée une figure pour afficher les 5 images cote à cote
    for i in range(len(liste_image)):
        imagebox = OffsetImage(liste_image[i], zoom=1) #on annote chaque subplot avec une image
        ab = AnnotationBbox(imagebox, (0.5, 0.5))  
        ax[i].add_artist(ab)
        ax[i].axis('off') #on fait disparaitre l'arriere plan grille
        Letitre="Note: "+str(round(listenote[i],1))+"/5 pour "+str(listenbnote[i])+" note(s)"
        ax[i].set_title(Letitre,fontdict = {'fontsize': 13,'fontweight' : 'bold'})
        #ax[i].text(0.1, 0.1, Letitre)
        #st.text(Letitre)
        
    return st.pyplot(fig)


#fonction globale 1
def recommandation_sys_1(movie):
    leresultat=recommand_5(movie)
    liste_movie = leresultat['title'].tolist()
    listenote=leresultat['moyenne'].tolist()
    listenbnote=leresultat['nb_rating'].tolist()
    liste_url = catch_url(liste_movie)
    liste_affiches = get_display_image(liste_url,listenote,listenbnote)
    return liste_affiches

#fonction globale 2
def recommandation_sys_2(movie):
    leresultat=corr_rate5(movie)
    liste_movie = leresultat['title'].tolist()
    listenote=leresultat['moyenne'].tolist()
    listenbnote=leresultat['nb_rating'].tolist()
    liste_url = catch_url(liste_movie)
    liste_affiches = get_display_image(liste_url,listenote,listenbnote)
    return liste_affiches

movie = input_sys_1()

st.header("Comment les utilisateurs définissent-ils ce film ?")

wordcloud(movie)


#recommandation 1
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

#recommandation 2
st.header('Les utilisateurs qui ont aimé ce film, ont aussi aimé...')



#recommandation 2
recommandation_sys_2(movie)


#statistiques
st.header('Quelques statistiques sur la base de données...')


#viz
image2 = Image.open('viz.png')

st.image(image2,
        use_column_width=True)

image3 = Image.open('viz2.png')

st.image(image3,
        use_column_width=True)