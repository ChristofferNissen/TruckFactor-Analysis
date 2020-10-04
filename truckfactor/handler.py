from pydriller import RepositoryMining
from datetime import datetime
import pyfiglet
import operator
import math
import emoji
import io
from contextlib import redirect_stdout
import json
import requests


# Async invocation example
# Open terminal 1 and run: 'nc -l 888'
# Open terminal 2 and run
'''
curl "https://gateway.christoffernissen.me/async-function/truckfactor" \
    --data '
    {
        "since": "None",
        "to": "2020-9-28-0-0",
        "urls": [
            "https://github.com/Praqma/helmsman.git",
            "https://github.com/ishepard/pydriller.git"
        ],
        "returnType": "Report",
        "excludes": [
            "Dockerfile",
            "/some/path"
        ] 
    }
    ' \
    --header "X-Callback-Url: http://192.168.1.112:8888"
'''

# Colors for terminal output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    ITA = '\033[3m'
    UNDERLINE = '\033[4m'


def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    def validateInput(req):
        # Validate Input
        if req == "" or not req.__contains__("urls") or not req.__contains__("since") or not req.__contains__("to") or not req.__contains__("returnType") or not req.__contains__("excludes"):
            return """ 
            Input missing. Please provide JSON as in this example:
            {
                "since": "None",
                "to": "2020-9-28-0-0",
                "urls": [
                    "https://github.com/Praqma/helmsman.git",
                    "https://github.com/ishepard/pydriller.git"
                ],
                "returnType": "Report",
                "excludes": [
                    "Dockerfile",
                    "/some/path"
                ]
            }
                note: returnType can also be Number for easy programmatic consumption 
                For multi url requests:
                    Report: Contatinated together to one response body
                    Number: Sum of tf for all repositories
            """
        else:
            return "OK"

    def parseJSON(json_string):
        # parse JSON input string
        data = json.loads(json_string)
        since = None
        sinceStr = data["since"]
        if not sinceStr == "None": 
            sinceArr = sinceStr.split("-")
            since = datetime(int(sinceArr[0]), int(sinceArr[1]), int(sinceArr[2]), int(sinceArr[3]), int(sinceArr[4])) 
        to = None
        toStr = data["to"]
        if not toStr == "None": 
            toArr = toStr.split("-")
            to = datetime(int(toArr[0]), int(toArr[1]), int(toArr[2]), int(toArr[3]), int(toArr[4])) 
        urls = data["urls"]
        returnType = data["returnType"]
        excludes = data["excludes"]
        return (since, to, urls, returnType, excludes)

    res = validateInput(req)
    if res == "OK":
        (since, to, urls, returnType, excludes) = parseJSON(req)
        return run_analysis(since, to, urls, returnType, excludes)
    else:
        return res
    
def run_analysis(since, to, urls, returnType, excludes):
    # Run Analysis. Aggregate report string and tf holder variable
    report = ""
    tf = 0
    for u in urls: 
        # redirect output to string variable
        f = io.StringIO()
        with redirect_stdout(f):
            tf = tf + analyse(since, to, u, excludes)
            
        out = f.getvalue()
        report = report + "\n" + out

    # output as Report or Number (API)
    if returnType == "Report":
        return report 
    elif returnType == "Number":  
        return tf
    else:
        return "Unsupported returnType. Use Report or Number"

def analyse(since, to, url, excludes):
    
    # PRINT FUNCTIONS

    def printIntro(project_name):
        # Print program information to user
        pyfiglet.print_figlet("VCS Analysis", font='slant')
        print("by Christoffer Nissen (ChristofferNissen)")
        print()
        print("Analyzing", url)
        print("Project Name:", project_name)
        print("Since:", since)
        print("To:", to)
        print("Total number of commits", count)
        print("Total number of merge commits", merges)
        print("Total number of authors", all_authors.__len__())
        print("Internal committers:", internal_authors.__len__())
        print("External committers:", external_authors.__len__())
        print("Specified exclude paths:")
        for ep in excludes:
            print(ep)

    def printLinguist(inclusion_list, responseText):
        pyfiglet.print_figlet("Linguist", font='small')
        print("Linguist generated inclusion_list with length", inclusion_list.__len__())
        print("Project Language Distribution:")
        print(responseText.strip())
        print()

    def printTop10Committers(collection):
        pyfiglet.print_figlet("The Top 10s", font='small')
        print("Top 10 committers")
        top10commiters = sorted(collection, key=collection.get, reverse=True)[:10]
        i = 1
        for tc in top10commiters:
            print("[",i,"]", "Email:", tc, "Count:", collection[tc], "Total %", collection[tc]/count*100)
            i = i + 1

    def printBottom10Committers(collection):
        print()
        print("Bottom comitters")
        bottom10commiters = sorted(collection, key=collection.get, reverse=False)[:10]
        i = 1
        for bc in bottom10commiters:
            print("[",i,"]", "Email:", bc, "Count:", collection[bc], "Total %", collection[bc]/count*100)
            i = i + 1

    def FileOverview():
        changes_per_file = CreateMapOfCommitAdditionsAndDeletesPerFileName()
        file_additions = sorted(changes_per_file, key=lambda tup: tup[1], reverse=True)[:10]
        file_deletions = sorted(changes_per_file, key=lambda tup: tup[2], reverse=True)[:10]

        print()
        print("Top 10 files with most additions")
        for line in file_additions:
            print(line)
        print()
        print("Top 10 files with most deletions")    
        for line in file_deletions:
            print(line)

    # DATA EXTRACTION

    def getInclusionListFromLinguist(url):
        def parseLinguistResponse(res):
            code_files = []
            for l in res:
                if not l.__contains__(":") and not l.__contains__("...") and not l.__contains__("%"):
                    code_files.append(l)
            return code_files

        responseText = requests.post('https://gateway.christoffernissen.me/function/linguist-caller', data=url).text
        linguist_analysis = responseText.split("\n")
        return (parseLinguistResponse(linguist_analysis), responseText)

    def ExtractFromCommits(since, to, url, excludes):
        # limit to time of writing script for reproduceable results
        commits = RepositoryMining(path_to_repo=url, since=since ,to=to)

        # Data extraction variables
        project_name = ""
        count = 0
        merges = 0
        all_authors = []
        author_commit_dict = dict()
        internal_authors = []
        external_authors = []
        code_changes = []
        iac_changes = []
        excluded_files = []
        for commit in commits.traverse_commits():
            if not project_name == "":
                project_name = commit.project_name 
            msg = commit.msg

            author = commit.author.email
            org_author = commit.committer.email
            count = count + 1
            
            if commit.merge:
                merges = merges + 1

            # extract files in this commit
            changedFiles = commit.modifications

            # remove files that match exclude paths
            files_for_analysis = changedFiles
            for file in changedFiles:
                path = ""

                if not file.new_path == None:
                    path = file.new_path
                else:
                    path = file.old_path
                
                for exclude_path in excludes:
                    # maybe handle wildcard here
                    print("exclude", exclude_path)
                    print("path", path)
                    print("in", exclude_path in path) 
                    if exclude_path in path:
                        if file in files_for_analysis:
                            files_for_analysis.remove(file)
                            if (file.filename, exclude_path) not in excluded_files:
                                excluded_files.append((file.filename, exclude_path))

            for file in files_for_analysis:
                filename = file.filename

                loc = file.nloc
                
                if not loc == None:
                    # code files
                    lines_added = file.added
                    lines_removed = file.removed
                    code_changes.append((commit.hash, author, filename, msg, lines_added, lines_removed, org_author))

                else:
                    # documentation and IAC files
                    lines_added = file.added
                    lines_removed = file.removed
                    iac_changes.append((commit.hash, author, filename, msg, lines_added, lines_removed, org_author))

            # Create overall collection of all authors independnt of company
            if not all_authors.__contains__(author):
                all_authors.append(author)
                author_commit_dict[author] = 1
            else:
                author_commit_dict[author] = author_commit_dict[author] + 1

            # split into internal and external
            if author.__contains__("eficode") or author.__contains__("praqma"):
                if not internal_authors.__contains__(author):
                    internal_authors.append(author)
            else:
                if not external_authors.__contains__(author):
                    external_authors.append(author)

        return (project_name, count, merges, all_authors, author_commit_dict, internal_authors, external_authors, code_changes, iac_changes, excluded_files)

    def CreateMapOfCommitAdditionsAndDeletesPerFileName():
        # collections to keep tmp count
        additions_per_file = dict()
        deletions_per_file = dict()

        # sort by filename
        sorted_filename = sorted(code_changes, key=lambda tup: tup[2])
        # line[2] = filename; line[4] = msg
        for line in sorted_filename:
            if not additions_per_file.__contains__(line[2]):
                additions_per_file[line[2]] = line[4]
            else:
                additions_per_file[line[2]] = additions_per_file[line[2]] + line[4]

            if not deletions_per_file.__contains__(line[2]):
                deletions_per_file[line[2]] = line[5]
            else:
                deletions_per_file[line[2]] = deletions_per_file[line[2]] + line[5]
                
        # aggregate changes from all authors to one collection of files with add and delete
        changes_per_file = []
        for line in sorted_filename:
            if not changes_per_file.__contains__((line[2], additions_per_file[line[2]], deletions_per_file[line[2]])):
                changes_per_file.append((line[2], additions_per_file[line[2]], deletions_per_file[line[2]]))

        return changes_per_file
    
    # Truck Factor Calculation

    def CalculateTruckFactor():
        print()
        pyfiglet.print_figlet("Ownership Calc.", font='small')
        print()

        def OrganizeData():

            # DOA calculation function from paper
            def DOA(FA, DL, AC):
                return (3.293 + 1.098 * FA + 0.164 * DL - 0.321 * math.log(1 + AC))

            def CalculateDLandAC(authors, org_author, dictionary):
                DL = 0
                AC = 0
                for a in authors:
                    if a == org_author:
                        DL = DL + dictionary[a]
                    else:
                        AC = AC + dictionary[a]
                return (DL, AC)

            # Convenience getters
            def GetRelatedChanges(filename):
                result = []
                for line in code_changes:
                    if line[2].__contains__(filename):
                        # we are looking for this line. Why not add it to a collection?
                        result.append(line)
                return result

            def GetAuthors(collection):
                result = []
                for line in collection:
                    if not result.__contains__(line[1]):
                        result.append(line[1])
                return result

            def GetAuthorsChanges(collection, author):
                result = []
                for line in collection:
                    if line[1] == author:
                        result.append(line)
                return result

            def GetFilesWithAbsoluteNoOfChanges():
                result = []
                for line in CreateMapOfCommitAdditionsAndDeletesPerFileName():
                    result.append((line[0], line[1]+line[2]))
                return result #sorted(result, key=lambda tup: tup[1], reverse=True)#[:10]

            def GetNormalizedDOAForEachAuthorOnEachFile():
                # Contains normalized DOA for each author on each file
                res = []

                files = sorted(GetFilesWithAbsoluteNoOfChanges(), key=lambda tup: tup[1], reverse=True)
                for line in files:
                    print("Currently processing", line)
                    fname = line[0]

                    def calculateFileOwnership(fname):
                        related_changes = GetRelatedChanges(fname)
                        print("Commits on this file", related_changes.__len__())

                        # Determine who is the creator of the file
                        org_author = related_changes[0][6]
                        authors = GetAuthors(related_changes)

                        print("No. of authors:", authors.__len__())

                        # calculate for this file per author
                        authorChanges = dict()
                        for a in authors:
                            changes = GetAuthorsChanges(related_changes, a)

                            total_lines_changed = 0
                            for c in changes:
                                total_lines_changed = total_lines_changed + c[4] + c[5]
                            authorChanges[a] = total_lines_changed

                        # calculate DOA for each contributere
                        result = []
                        for a in authors:
                            # FA = 1 if d is the creator if the file
                            # DL number of changes made to this file by the d
                            # AC total number of changes made by other developers
                            FA = 0
                            if a == org_author:
                                FA = 1
                            
                            (DL, AC) = CalculateDLandAC(authors, a, authorChanges)
                            doa = DOA(FA, DL, AC)
                            #print("DOA", doa, "FA", FA, "DL", DL, "AC", AC)

                            result.append((a, doa))
                        return result

                    def StandardizeValues(collection):
                        # normalize value. calculate Z
                        # z = (x - mean) / s (standard deviation)
                        def sum(dataset):
                            total = 0
                            for d in dataset:
                                total = total + d[1]
                            return total

                        def mean(dataset):
                            total = sum(dataset)
                            return total / dataset.__len__() - 1

                        def CalculateStdiv(collection):
                            n = collection.__len__() 
                            sumOfDoa = sum(collection)
                            squared = sumOfDoa * sumOfDoa
                            sumSquared = 0
                            for r in collection:
                                sumSquared = sumSquared + (r[1] * r[1])

                            if (n - 1) <= 0:
                                # some weird edge cases happen on large repos where sumSquared == squared. Not set it to one for know, no thorughts behind.
                                variance = 1
                            else:
                                variance = (sumSquared - (squared / n)) / (n - 1)

                            stdiv = math.sqrt(variance)
                            return stdiv

                        # standard deviation
                        # s = sqrt((sum(x-mean)^2)/n-1)
                        mean = mean(collection)
                        stdiv = CalculateStdiv(collection)
                        
                        res = []
                        for r in collection:
                            doa = r[1]
                            z = (doa - mean) / stdiv
                            res.append((r[0], z))
                        return res

                    def NormalizeValues(collection):
                        # x = (x - x_min) / (x_max - x_min)
                        result = []
                        max_v = sorted(collection, key=lambda tup: tup[1], reverse=True)[:1]
                        min_v = sorted(collection, key=lambda tup: tup[1], reverse=False)[:1]
                        x_min = min_v[0][1]
                        x_max = max_v[0][1]

                        for e in collection:
                            x = e[1]
                            if not x_max == x_min:
                                x_new = (x - x_min) / (x_max - x_min)
                            else: 
                                x_new = 1
                            result.append((e[0],x_new))
                        return result

                    def combineResults(list1, list2):
                        res = []
                        for i in range(list1.__len__()):
                            r1 = list1[i]
                            r2 = list2[i]
                            res.append((r1[0], r1[1], r2[1]))
                        return res

                    file_ownership = calculateFileOwnership(fname)
                    file_ownership_normalized = NormalizeValues(file_ownership)
                    file_ownership_standardized = StandardizeValues(file_ownership)
                    combined = combineResults(file_ownership_normalized, file_ownership_standardized)

                    print("Calculating DOA for file", fname)
                    print("(Author, Normalized, Standardized)")
                    doa_normalized_standardized_sorted = sorted(combined, key=lambda tup: tup[1], reverse=True)[:5]
                    for l in doa_normalized_standardized_sorted:
                        if l[1] > 0.75:
                            print(f"{bcolors.OKGREEN}--> {l}{bcolors.ENDC}")
                        else:
                            print("-->", l)

                    print()
                    doa_normalized_sorted = sorted(file_ownership_normalized, key=lambda tup: tup[1], reverse=True)[:5]
                    res.append((fname, doa_normalized_sorted))
                
                return res
            
            return GetNormalizedDOAForEachAuthorOnEachFile()

        def ParseOrganizedData(file_author_doa, inclusion_list):
            fileWithFileAuthor = []
            fileAuthors = []
            filesWithAuthors = []
            authorAndCount = []

            print("Linguist file overview")
            print("No. of analyzed files:", file_author_doa.__len__())
            for fd in file_author_doa:
                print(f"{bcolors.OKGREEN}{fd[0]}{bcolors.ENDC}")
            #print("Missing from Linguist-analysis")
            tmp_inclusion_list = inclusion_list
            for fd in file_author_doa:
                file = fd[0]
                for e in tmp_inclusion_list:
                    arr = e.split("/")
                    filename = arr[arr.__len__()-1]
                    if filename.__contains__(file):
                        tmp_inclusion_list.remove(e)
            
            for i in tmp_inclusion_list:
                val = i.replace("\n", "")
                # different print for files excluded explicitly
                explicitlyExcluded = False
                res = ""
                for e in excluded_files:
                    filename = e[0]
                    if val.__contains__(filename):
                        explicitlyExcluded = True
                        excludedBy = "excluded by " + e[1]
                        res = filename + f"{bcolors.ITA}{excludedBy}{bcolors.ENDC}"
                        break
                if explicitlyExcluded:
                    print(f"{bcolors.OKBLUE}{res}{bcolors.ENDC}") 
                elif not i == "":
                    print(f"{bcolors.FAIL}{val}{bcolors.ENDC}")

            if excluded_files.__len__() > 0:
                print("Excluded files")
                print("(filename, excluded_by_path)")
            for e in excluded_files:
                filename = e[0]
                if not filename == "":
                    print(f"{bcolors.WARNING}{e}{bcolors.ENDC}")

            print()
            print("No. of authors", all_authors.__len__())
            for a in all_authors:           
                count = 0
                for e in file_author_doa:
                    fileName = e[0]
                    AuthorDoaListForFile = e[1]
                    for t in AuthorDoaListForFile:
                        author = t[0]
                        normalizeddoa = t[1]
                        if author == a:
                            if normalizeddoa > 0.75:
                                count = count + 1

                                if not filesWithAuthors.__contains__(fileName):
                                    filesWithAuthors.append(fileName)

                                if not fileAuthors.__contains__(a):
                                    fileAuthors.append(a)

                                fileWithFileAuthor.append((fileName, a))

                authorAndCount.append((a, count))
            
            return(fileWithFileAuthor, fileAuthors, filesWithAuthors, authorAndCount)
        
        def printNumberOfAuthors(alist):
            print("No. of authors with ownership", alist.__len__())

        def printAuthorInformation(collection):
            print("Author(s) with file ownership:")

            sortedCollection = sorted(collection, key=lambda tup: tup[1])

            for t in sortedCollection:
                a = t[0]
                count = t[1]
                if count > 0:
                    print("Author", a)
                    print("Owner of ", count, "files")

        def calculateFactor(authorWithOwnershipCount, fileWithFileAuthorsMap, file_author_doa):
            # Check that 0.5 of files have an author
            # Loop over files and count each time a file has an author
            # we have a touple of (file, author) for each ownership
            tf = 0
            for t_ac in authorWithOwnershipCount:
                a = t_ac[0]
                c = t_ac[1]
                
                # count unique files with authors
                uq = 0
                seenFiles = []
                for t in fileWithFileAuthorsMap:
                    f = t[0]
                    if not seenFiles.__contains__(f):
                        seenFiles.append(f)
                        uq = uq + 1

                ratio = uq / file_author_doa.__len__()

                if ratio > 0.5:
                    tf = tf + 1 
                    # remove author tuples
                    tmp = []
                    for v in fileWithFileAuthorsMap:
                        author = v[1]
                        if not author == a:
                            tmp.append(v)
                    fileWithFileAuthorsMap = tmp
                else:
                    break

            return tf

        file_author_doa = OrganizeData()    
        (fileWithFileAuthor, fileAuthors, _, authorAndCount) = ParseOrganizedData(file_author_doa, inclusion_list)

        pyfiglet.print_figlet("Truck Factor Calc.", font='small')
        print()
        printNumberOfAuthors(fileAuthors)
        printAuthorInformation(authorAndCount)

        # sort by count
        authorAndCount = sorted(authorAndCount, key=lambda tup: tup[1], reverse=True)
        tf = calculateFactor(authorAndCount, fileWithFileAuthor, file_author_doa)

        print()
        print("The Truck Factor for this project is")
        print()
        pyfiglet.print_figlet("  //  " + str(tf) + "  //  ", font='univers')
        
        if tf < 2:
            print("Your project has a low truck factor. Only a single person have to leave the project for it to be in serious danger due to lack of maintainers")

        print()
        return tf

    # PROGRAM FLOW
    (inclusion_list, responseText) = getInclusionListFromLinguist(url)

    (project_name, count, merges, all_authors, author_commit_dict, 
    internal_authors, external_authors, code_changes, _, excluded_files) = ExtractFromCommits(since, to, url, excludes)

    printIntro(project_name)
    printLinguist(inclusion_list, responseText)
    printTop10Committers(author_commit_dict)
    #printBottom10Committers(author_commit_dict)
    FileOverview()
    return CalculateTruckFactor()
    # PROGRAM END
