import sys
from django.shortcuts import render
from movieRec import utility
import pandas as pd
import re


def index(request):
    return render(request, 'index.html')


def searchResults(request):
    if request.method == 'POST':
        movieTitle = request.POST.get('movieTitle', '')
    else:
        movieTitle = ''

    print("Loading data from files, please wait...")
    try:
        path = 'data/movies.csv'
        columnNames = ['MovieID', 'Title', 'Genres']
        dfMovies = pd.read_csv(path, sep=',', encoding='ISO-8859-1', names=columnNames, header=None, engine='python')
        movies = list(dfMovies['Title'])
        moviesFound = []
        for movie in movies:
            # Removing the year for the comparison
            # Computing the levenshteinDistance and searching also for patterns in the titles
            if utility.Module.levenshteinDistance(movie[:-7], movieTitle) < 0.45 or re.search(movieTitle, movie[:-7]):
                moviesFound.append(movie)
        # results in alphabetical order
        moviesFound.sort()
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
