import sys
from django.shortcuts import render
from sklearn.feature_extraction.text import TfidfVectorizer
from movieRec import utility
import pandas as pd
import numpy as np
import re


# Sorting list of tuples according to a key
def secondItem(n):
    return n[1]


# function to sort the tuple
def sortBySecondItem(list_of_tuples):
    return sorted(list_of_tuples, key=secondItem)


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

        path = 'data/extracted_custom.csv'
        columnNames = ['MovieID', 'Actors', 'Synopsis', 'Plot']
        dfFeatures = pd.read_csv(path, sep='§', quoting=3, encoding='utf8', names=columnNames, header=None,
                                 engine='python')

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
                    movie_plot = dfFeatures.loc[dfFeatures['MovieID'] == int(movieId), 'Plot'].values[0]
                    moviesFound.append((
                        movieId,
                        movie_info.iloc[0]['Title'],
                        movie_info.iloc[0]['Genres'],
                        movie_plot,
                        (lambda item: item.iloc[0]['Poster'] if (not item.empty) else utility.Module.posterNotFoundUrl)
                        (movie_poster),
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
        # <editor-fold desc="Loading datas">
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

        path = 'data/genomes_custom.csv'
        columnNames = ['MovieID', 'TagID', 'Relevance']
        dfGenomes = pd.read_csv(path, sep=',', names=columnNames, header=None, engine='python')

        popularityDictionary = dfRatings.groupby(['MovieID'])['MovieID'].count().to_dict()
        popularityList = list(popularityDictionary.items())
        popularityList = sortBySecondItem(popularityList)
        # </editor-fold>

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
            sim = utility.Module.kulczynskiSim(row_genres1, row_genres2)
            moviesSim.append((item[0], sim))
        # sorting the results by similarity
        moviesSim = sortBySecondItem(moviesSim)
        # get last 20 movies sorted by similarity crescent
        moviesRecommended = moviesSim[-20:]

        moviesRecommendedWithPopularity = []
        counter = 0
        for popularMovie in popularityList:
            for movieRecommended in moviesRecommended:
                # if the popular movie is in the recommended list
                if str(popularMovie[0]) == movieRecommended[0]:
                    # I take it
                    moviesRecommendedWithPopularity.append(movieRecommended)
                    counter = counter + 1
                    # I stop searching the recommended list
                    break
            # if I have already taken five elements, I will stop
            if counter == 5:
                break

        res1 = []
        for movie in moviesRecommendedWithPopularity:
            idRecommendation = movie[0]
            title = dfMovies.loc[dfMovies['MovieID'] == idRecommendation, 'Title'].values[0]
            genres = dfMovies.loc[dfMovies['MovieID'] == idRecommendation, 'Genres'].values[0]
            movie_poster = dfPosters[dfPosters['MovieID'] == int(idRecommendation)]
            plot = dfFeatures.loc[dfFeatures['MovieID'] == int(idRecommendation), 'Plot'].values[0]
            res1.append(((lambda item: item.iloc[0]['Poster'] if (not item.empty) else utility.Module.posterNotFoundUrl)
                         (movie_poster),
                         title,
                         genres,
                         plot))
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

        # I take first 10 movies indexes by sim (the current movie is included,
        # I will not take it into the final output)
        resultIndexes = np.argpartition(rowSim, -10)[-10:]

        res2 = []
        counter = 0
        for popularMovie in popularityList:
            for movieRecommended in resultIndexes:
                # I take the corresponding plot of the index in the corpus
                plotFound = corpus[movieRecommended]
                # I retrieve the MovieID by the plot
                movieIdFound = str(dfFeatures.loc[dfFeatures['Plot'] == plotFound, 'MovieID'].values[0])
                # if the popular movie is in the recommended list AND
                # it is not the one selected before
                if str(popularMovie[0]) == movieIdFound and not movieIdFound == movieID:
                    # I take it
                    title = dfMovies.loc[dfMovies['MovieID'] == movieIdFound, 'Title'].values[0]
                    genres = dfMovies.loc[dfMovies['MovieID'] == movieIdFound, 'Genres'].values[0]
                    movie_poster = dfPosters[dfPosters['MovieID'] == int(movieIdFound)]
                    plot = dfFeatures.loc[dfFeatures['MovieID'] == int(movieIdFound), 'Plot'].values[0]
                    res2.append(((lambda item: item.iloc[0]['Poster'] if (not item.empty) else utility.Module.posterNotFoundUrl)
                                 (movie_poster),
                                 title,
                                 genres,
                                 plot))
                    counter = counter + 1
                    # I stop searching the recommended list
                    break
            # if I have already taken five elements, I will stop
            if counter == 5:
                break
        # </editor-fold>

        # <editor-fold desc="Synopsis Similarity">
        currentSynopsis = dfFeatures.loc[dfFeatures['MovieID'] == int(movieID), 'Synopsis'].values[0]
        # creating the list of texts for the tf.idf, ignoring empty plots
        corpus = list(dfFeatures['Synopsis'])
        corpus = [str(val) for val in corpus if val is not None]
        # compute similarity between texts
        # from https://stackoverflow.com/questions/8897593/how-to-compute-the-similarity-between-two-text-documents
        vect = TfidfVectorizer(min_df=1, stop_words="english")
        tfidf = vect.fit_transform(corpus)
        pairwise_similarity = tfidf * tfidf.T
        arraySim = pairwise_similarity.toarray()

        # taking the row for the current synopsis
        input_idx = corpus.index(currentSynopsis)
        rowSim = arraySim[input_idx]

        # I take first 10 movies indexes by sim (the current movie is included,
        # I will not take it into the final output)
        resultIndexes = np.argpartition(rowSim, -10)[-10:]

        res3 = []
        counter = 0
        for popularMovie in popularityList:
            for movieRecommended in resultIndexes:
                # I take the corresponding plot of the index in the corpus
                synopsisFound = corpus[movieRecommended]
                # I retrieve the MovieID by the plot
                movieIdFound = str(dfFeatures.loc[dfFeatures['Synopsis'] == synopsisFound, 'MovieID'].values[0])
                # if the popular movie is in the recommended list AND
                # it is not the one selected before
                if str(popularMovie[0]) == movieIdFound and not movieIdFound == movieID:
                    # I take it
                    title = dfMovies.loc[dfMovies['MovieID'] == movieIdFound, 'Title'].values[0]
                    genres = dfMovies.loc[dfMovies['MovieID'] == movieIdFound, 'Genres'].values[0]
                    movie_poster = dfPosters[dfPosters['MovieID'] == int(movieIdFound)]
                    plot = dfFeatures.loc[dfFeatures['MovieID'] == int(movieIdFound), 'Plot'].values[0]
                    res3.append(((lambda item: item.iloc[0]['Poster'] if (not item.empty) else utility.Module.posterNotFoundUrl)
                                 (movie_poster),
                                 title,
                                 genres,
                                 plot))
                    counter = counter + 1
                    # I stop searching the recommended list
                    break
            # if I have already taken five elements, I will stop
            if counter == 5:
                break
        # </editor-fold>

        # <editor-fold desc="Actors Similarity">
        selectedActors = dfFeatures.loc[dfFeatures['MovieID'] == int(movieID), 'Actors'].values[0]
        # extracting id and genre from the pool
        idActors = list(zip(dfFeatures.MovieID, dfFeatures.Actors))

        moviesSim = []
        # converting the selected genres into a list
        row_actors1 = selectedActors.split('|')
        for item in idActors:
            if not pd.isna(item[1]):
                row_actors2 = item[1].split('|')
                sim = utility.Module.kulczynskiSim(row_actors1, row_actors2)
            else:
                sim = 0
            moviesSim.append((item[0], sim))
        # sorting the results by similarity
        moviesSim = sortBySecondItem(moviesSim)
        # get last 20 movies sorted by similarity crescent
        moviesRecommended = moviesSim[-20:]

        moviesRecommendedWithPopularity = []
        counter = 0
        for popularMovie in popularityList:
            for movieRecommended in moviesRecommended:
                # if the popular movie is in the recommended list
                if popularMovie[0] == movieRecommended[0]:
                    # I take it
                    moviesRecommendedWithPopularity.append(movieRecommended)
                    counter = counter + 1
                    # I stop searching the recommended list
                    break
            # if I have already taken five elements, I will stop
            if counter == 5:
                break

        res4 = []
        for movie in moviesRecommendedWithPopularity:
            idRecommendation = str(movie[0])
            title = dfMovies.loc[dfMovies['MovieID'] == idRecommendation, 'Title'].values[0]
            genres = dfMovies.loc[dfMovies['MovieID'] == idRecommendation, 'Genres'].values[0]
            movie_poster = dfPosters[dfPosters['MovieID'] == int(idRecommendation)]
            plot = dfFeatures.loc[dfFeatures['MovieID'] == int(idRecommendation), 'Plot'].values[0]
            res4.append(((lambda item: item.iloc[0]['Poster'] if (not item.empty) else utility.Module.posterNotFoundUrl)
                         (movie_poster),
                         title,
                         genres,
                         plot))
        # </editor-fold>

        # <editor-fold desc="Keywords Similarity">
        selectedTags = dfGenomes.loc[dfGenomes['MovieID'] == movieID, 'TagID']
        selected_tags = selectedTags.tolist()

        idTags = list(zip(dfGenomes.MovieID, dfGenomes.TagID, dfGenomes.Relevance))
        movies_tags = {}

        # retrieving the tags for each MovieId
        for movie_id, tag_id, _ in idTags:
            if movie_id not in movies_tags:
                movies_tags[movie_id] = set()
            movies_tags[movie_id].add(tag_id)

        #calculating the similarity between the set of tags of the selected MovieID and the dataset
        moviesSim = []
        for movie_id, row_tags in movies_tags.items():
            sim = utility.Module.kulczynskiSim(selected_tags, row_tags)
            moviesSim.append((movie_id, sim))

        # sorting the results by similarity
        moviesSim = sortBySecondItem(moviesSim)

        # get last 20 movies sorted by similarity crescent
        moviesRecommended = moviesSim[-20:]

        moviesRecommendedWithPopularity = []
        counter = 0

        for popularMovie in popularityList:
            for movieRecommended in moviesRecommended:
                # if the popular movie is in the recommended list
                if popularMovie[0] == int(movieRecommended[0]):
                    # I take it
                    moviesRecommendedWithPopularity.append(movieRecommended)
                    counter = counter + 1
                    # I stop searching the recommended list
                    break
            # if I have already taken five elements, I will stop
            if counter == 5:
                break

        res5 = []

        for movie in moviesRecommendedWithPopularity:
            idRecommendation = str(movie[0])
            title = dfMovies.loc[dfMovies['MovieID'] == idRecommendation, 'Title'].values[0]
            genres = dfMovies.loc[dfMovies['MovieID'] == idRecommendation, 'Genres'].values[0]
            movie_poster = dfPosters[dfPosters['MovieID'] == int(idRecommendation)]
            plot = dfFeatures.loc[dfFeatures['MovieID'] == int(idRecommendation), 'Plot'].values[0]
            if len(title) > 0 and len(genres) > 0 and idRecommendation != movieID:
                res5.append(((lambda item: item.iloc[0]['Poster'] if (not item.empty) else utility.Module.posterNotFoundUrl)
                             (movie_poster),
                             title,
                             genres,
                             plot))
                counter = counter + 1
        # </editor-fold>

        context = {
            'moviesGenres': res1,
            'moviesPlot': res2,
            'moviesSynopsis': res3,
            'moviesActors': res4,
            'moviesKeywords': res5
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
