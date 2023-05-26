import sys
from django.shortcuts import render
from movieRec import utility
import pandas as pd


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
        print('Test commit')
        for movie in movies:
            # I remove the year for the comparison
            # TO DO: improving matching like searching also for regular expression in it
            if utility.Module.similar(movie[:-7], movieTitle) >= 0.8:
                moviesFound.append(movie)

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
