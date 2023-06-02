import sys
from django.shortcuts import render
from movieRec import utility
import pandas as pd
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
        path = 'data/movies.dat'
        columnNames = ['MovieID', 'Title', 'Genres']
        dfMovies = pd.read_csv(path, sep='::', encoding='ISO-8859-1', names=columnNames, header=None, engine='python')

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
                    movieId = movie_info.iloc[0]['MovieID']
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

    # need to convert it to int otherwise the drop() below will not work
    movieIDint = int(movieID)
    try:
        path = 'data/movies.dat'
        columnNames = ['MovieID', 'Title', 'Genres']
        dfMovies = pd.read_csv(path, sep='::', encoding='ISO-8859-1', names=columnNames, header=None, engine='python')

        path = 'data/movie_poster.csv'
        columnNames = ['MovieID', 'Poster']
        dfPosters = pd.read_csv(path, sep=',', names=columnNames, header=None, engine='python')

        path = 'data/movie_url.csv'
        columnNames = ['MovieID', 'Url']
        dfUrls = pd.read_csv(path, sep=',', names=columnNames, header=None, engine='python')

        path = 'data/ratings.dat'
        columnNames = ['UserID', 'MovieID', 'Rating', 'TimeStamp']
        dfRatings = pd.read_csv(path, sep='::', names=columnNames, header=None, engine='python')

        selectedGenres = dfMovies.loc[dfMovies['MovieID'] == movieIDint, 'Genres'].values[0]

        # remove the selected movie from the recommendations pool
        dfMovies.drop(dfMovies[dfMovies['MovieID'] == movieIDint].index, inplace=True)
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
        # Get last 5 movies sorted by similarity crescent
        moviesRecommended = moviesSim[-5:]

        res = []
        for movie in moviesRecommended:
            idRecommendation = movie[0]
            title = dfMovies.loc[dfMovies['MovieID'] == idRecommendation, 'Title'].values[0]
            genres = dfMovies.loc[dfMovies['MovieID'] == idRecommendation, 'Genres'].values[0]
            res.append((idRecommendation, title, genres))
        context = {
            'movies': res,
        }
        return render(request, 'recommendations.html', context)
    except FileNotFoundError:
        print(f"File {path} not found!", file=sys.stderr)
        # TODO: return page error
        moviesRecommended = []
        context = {
            'movies': moviesRecommended,
        }
        return render(request, 'index.html', context)
    except PermissionError:
        print(f"Insufficient permission to read {path}!", file=sys.stderr)
        # TODO: return page error
        moviesRecommended = []
        context = {
            'movies': moviesRecommended,
        }
        return render(request, 'index.html', context)
    except IsADirectoryError:
        print(f"{path} is a directory!", file=sys.stderr)
        # TODO: return page error
        moviesRecommended = []
        context = {
            'movies': moviesRecommended,
        }
        return render(request, 'index.html', context)
