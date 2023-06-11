import sys
from django.shortcuts import render
from sklearn.feature_extraction.text import TfidfVectorizer
from movieRec import utility
import pandas as pd
import numpy as np
import re

# Sorting list of tuples according to a key
def similarity(n):
    return n[1]

# function to sort the tuple
def sort_by_similarity(list_of_tuples):
    return sorted(list_of_tuples, key=similarity)

def index(request):
    return render(request, 'index.html')

def searchResults(request):
    if request.method == 'POST':
        movieTitle = request.POST.get('movieTitle', '')
    else:
        movieTitle = ''

    print("Loading data from files, please wait...")
    try:
        path = 'data/movies_custom.csv'
        columnNames = ['MovieID', 'Title', 'Genres']
        dfMovies = pd.read_csv(path, sep=',', names=columnNames, header=None, engine='python')

        path = 'data/movie_poster.csv'
        columnNames = ['MovieID', 'Poster']
        dfPosters = pd.read_csv(path, sep=',', names=columnNames, header=None, engine='python')

        path = 'data/movie_url.csv'
        columnNames = ['MovieID', 'Url']
        dfUrls = pd.read_csv(path, sep=',', names=columnNames, header=None, engine='python')
        titles = list(dfMovies['Title'])

        moviesFound = []
        for movie in titles:
            # Removing the year for the comparison
            # Computing the levenshteinDistance and searching also for patterns in the titles
            if utility.Module.levenshteinDistance(movie[:-7], movieTitle) < 0.45 or re.search(movieTitle, movie[:-7]):
                movie_info = dfMovies[dfMovies['Title'] == movie]
                if not movie_info.empty:
                    movieId = int(movie_info.iloc[0]['MovieID'])
                    movie_poster = dfPosters[dfPosters['MovieID'] == movieId]
                    movie_url = dfUrls[dfUrls['MovieID'] == movieId]
                    moviesFound.append((
                        movieId,
                        movie_info.iloc[0]['Title'],
                        movie_info.iloc[0]['Genres'],
                        (lambda item: item.iloc[0]['Poster'] if (not item.empty) else 'Broken')(movie_poster),
                        (lambda item: item.iloc[0]['Url'] if (not item.empty) else "linkNotFound")(movie_url)
                    ))
        # results in alphabetical order
        # TODO: sort tuple
        # moviesFound.sort()

        context = {
            'movies': moviesFound,
        }
        return render(request, 'search_results.html', context)
    except FileNotFoundError:
        print(f"File {path} not found!", file=sys.stderr)
        # TO DO: return page error
        moviesFound = []
        context = {
            'movies': moviesFound,
        }
        return render(request, 'search_results.html', context)
    except PermissionError:
        print(f"Insufficient permission to read {path}!", file=sys.stderr)
        # TO DO: return page error
        moviesFound = []
        context = {
            'movies': moviesFound,
        }
        return render(request, 'search_results.html', context)
    except IsADirectoryError:
        print(f"{path} is a directory!", file=sys.stderr)
        # TO DO: return page error
        moviesFound = []
        context = {
            'movies': moviesFound,
        }
        return render(request, 'search_results.html', context)

def recommendations(request):
    if request.method == 'POST':
        movieID = request.POST.get('movieID', '')
    else:
        movieID = ''

    if not movieID.isnumeric():
        # TODO: return page error
        return render(request, 'index.html')

    try:
        path = 'data/movies_custom.csv'
        columnNames = ['MovieID', 'Title', 'Genres']
        dfMovies = pd.read_csv(path, sep=',', names=columnNames, header=None, engine='python')

        path = 'data/movie_poster.csv'
        columnNames = ['MovieID', 'Poster']
        dfPosters = pd.read_csv(path, sep=',', names=columnNames, header=None, engine='python')

        path = 'data/movie_url.csv'
        columnNames = ['MovieID', 'Url']
        dfUrls = pd.read_csv(path, sep=',', names=columnNames, header=None, engine='python')

        path = 'data/ratings.dat'
        columnNames = ['UserID', 'MovieID', 'Rating', 'TimeStamp']
        dfRatings = pd.read_csv(path, sep='::', names=columnNames, header=None, engine='python')

        path = 'data/extracted_custom.csv'
        columnNames = ['MovieID', 'Actors', 'Synopsis', 'Plot']
        dfFeatures = pd.read_csv(path, sep='§', quoting=3, encoding='utf8', names=columnNames, header=None,
                                 engine='python')

        # <editor-fold desc="Genre Similarity">
        selectedGenres = dfMovies.loc[dfMovies['MovieID'] == movieID, 'Genres'].values[0]

        # remove the selected movie from the recommendations pool
        dfMovies.drop(dfMovies[dfMovies['MovieID'] == movieID].index, inplace=True)
        # extracting id and genre from the pool
        idGenres = list(zip(dfMovies.MovieID, dfMovies.Genres))

        moviesSim = []
        # converting the selected genres into a list
        row_genres1 = selectedGenres.split('|')
        for item in idGenres:
            row_genres2 = item[1].split('|')
            sim = utility.Module.jaccardSim(row_genres1, row_genres2)
            moviesSim.append((item[0], sim))
        # sorting the results by similarity
        moviesSim = sort_by_similarity(moviesSim)
        # get last 5 movies sorted by similarity crescent
        moviesRecommended = moviesSim[-5:]

        res1 = []
        for movie in moviesRecommended:
            idRecommendation = movie[0]
            title = dfMovies.loc[dfMovies['MovieID'] == idRecommendation, 'Title'].values[0]
            genres = dfMovies.loc[dfMovies['MovieID'] == idRecommendation, 'Genres'].values[0]
            res1.append((idRecommendation, title, genres))
        # </editor-fold>

        # <editor-fold desc="Plot Similarity">
        currentPlot = dfFeatures.loc[dfFeatures['MovieID'] == int(movieID), 'Plot'].values[0]
        # creating the list of texts for the tf.idf, ignoring empty plots
        corpus = list(dfFeatures['Plot'])
        corpus = [str(val) for val in corpus if val is not None]
        # compute similarity between texts
        # from https://stackoverflow.com/questions/8897593/how-to-compute-the-similarity-between-two-text-documents
        vect = TfidfVectorizer(min_df=1, stop_words="english")
        tfidf = vect.fit_transform(corpus)
        pairwise_similarity = tfidf * tfidf.T
        arraySim = pairwise_similarity.toarray()

        # taking the row for the current plot
        input_idx = corpus.index(currentPlot)
        rowSim = arraySim[input_idx]

        # I take first 6 movies indexes by sim (the current movie is included, I will not take it into the final output)
        resultIndexes = np.argpartition(rowSim, -6)[-6:]

        res2 = []
        for idx in resultIndexes:
            plotFound = corpus[idx]
            movieIdFound = str(dfFeatures.loc[dfFeatures['Plot'] == plotFound, 'MovieID'].values[0])
            # I exclude the selected movie on the previous page
            if not movieIdFound == movieID:
                title = dfMovies.loc[dfMovies['MovieID'] == movieIdFound, 'Title'].values[0]
                genres = dfMovies.loc[dfMovies['MovieID'] == movieIdFound, 'Genres'].values[0]
                res2.append((movieIdFound, title, genres))
        # </editor-fold>

        context = {
            'moviesGenres': res1,
            'moviesPlot': res2
        }
        return render(request, 'recommendations.html', context)
    except FileNotFoundError:
        print(f"File {path} not found!", file=sys.stderr)
        # TODO: return page error
        moviesRecommended = []
        context = {
            'moviesGenres': moviesRecommended,
        }
        return render(request, 'index.html', context)
    except PermissionError:
        print(f"Insufficient permission to read {path}!", file=sys.stderr)
        # TODO: return page error
        moviesRecommended = []
        context = {
            'moviesGenres': moviesRecommended,
        }
        return render(request, 'index.html', context)
    except IsADirectoryError:
        print(f"{path} is a directory!", file=sys.stderr)
        # TODO: return page error
        moviesRecommended = []
        context = {
            'moviesGenres': moviesRecommended,
        }
        return render(request, 'index.html', context)
