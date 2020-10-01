from pydriller import RepositoryMining
from datetime import datetime
import pyfiglet
import operator
import math
import emoji
import io
from contextlib import redirect_stdout
import json

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    # json draft
    {
        "since": "None",
        "to": "2020-9-28-0,0",
        "urls": [
            "https://github.com/Praqma/helmsman.git",
            "https://github.com/ishepard/pydriller.git"
        ]
    }

    # curl "https://gateway.christoffernissen.me/async-function/truckfactor" \
    #     --data "
    #     {
    #         "since": "None",
    #         "to": "2020-9-28-0,0",
    #         "urls": [
    #             "https://github.com/Praqma/helmsman.git",
    #             "https://github.com/ishepard/pydriller.git"
    #         ]
    #     }
    #     " \
    #     --header "X-Callback-Url: http://192.168.1.112:8888"

    data = json.loads(req)
    since = None
    sinceStr = data["since"]
    if not sinceStr == "None": 
        sinceArr = sinceStr.split("-")
        since = datetime(int(sinceArr[0]), int(sinceArr[1]), int(sinceArr[2]), int(sinceArr[3]), int(sinceArr[4])) 

    toStr = data["to"]
    if not toStr == "None": 
        toArr = toStr.split("-")
        to = datetime(int(toArr[0]), int(toArr[1]), int(toArr[2]), int(toArr[3]), int(toArr[4])) 
        
    urls = data["urls"]

    print("")
    print("Input parse results")
    print(since)
    print(to)
    print(urls)
    print("")

    f = io.StringIO()
    with redirect_stdout(f):
        
        #urls = ["repos/repo1", "repos/repo2", "https://github.com/ishepard/pydriller.git", "repos/repo3", "https://github.com/apache/hadoop.git"]
        #urls = ["https://github.com/ishepard/pydriller.git"]
        urls = ["https://github.com/Praqma/helmsman.git"]
        since = None
        to = datetime(2020, 9, 28, 0, 0)
        main(since, to, urls)
        
    out = f.getvalue()  
    return out 


# Colors for terminal output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# DOA calculation function
def DOA(FA, DL, AC):
    return (3.293 + 1.098 * FA + 0.164 * DL - 0.321 * math.log(1 + AC))

# Main loop
def main(since, to, urls):

    # limit to time of writing script for reproduceable results
    commits = RepositoryMining(path_to_repo=urls, since=since ,to=to)

    count = 0       # number of commits
    merges = 0      # number of merges
    all_authors = []
    author_commit_dict = dict()
    internal_authors = []
    external_authors = []
    code_changes = []
    iac_changes = []
    for commit in commits.traverse_commits():
        msg = commit.msg

        author = commit.author.email
        org_author = commit.committer.email
        count = count + 1
        
        if commit.merge:
            merges = merges + 1

        # extract files in this commit
        changedFiles = commit.modifications
        for file in changedFiles:
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

    # for loop end.
    # VCS commit parse done


    def printIntro():
        # Print program information to user
        print()
        pyfiglet.print_figlet("VCS Analysis")
        print("by Christoffer Nissen (ChristofferNissen)")
        print()
        print()
        print("Analysing", urls)
        print("Project Name:", commit.project_name)
        print("Since:", since)
        print("To:", to)
        print("Total number of commits", count)
        print("Total number of merge commits", merges)
        print("Total number of authors", all_authors.__len__())
        print("Internal committers:", internal_authors.__len__())
        print("External committers:", external_authors.__len__())

    def printTop10Committers(collection):
        print()
        print("Top committers")
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

    # Methods for DOA calculations for top 10 source code files

    def CreateMapOfCommitAdditionsAndDeletesPerFileName():
        # collections to keep tmp count
        additions_per_file = dict()
        deletions_per_file = dict()

        # sort by filename
        sorted_filename = sorted(code_changes, key=lambda tup: tup[2])
        # line[2] = filename
        # line[4] = msg
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
    
    def GetTop10Files():
        result = []
        for line in CreateMapOfCommitAdditionsAndDeletesPerFileName():
            result.append((line[0], line[1]+line[2]))
        return result #sorted(result, key=lambda tup: tup[1], reverse=True)#[:10]

    def FileOverview():
        changes_per_file = CreateMapOfCommitAdditionsAndDeletesPerFileName()
        file_additions = sorted(changes_per_file, key=lambda tup: tup[1], reverse=True)[:10]
        file_deletions = sorted(changes_per_file, key=lambda tup: tup[2], reverse=True)[:10]

        print()
        print("Top files with most additions")
        for line in file_additions:
            print(line)
        print()
        print("Top files with most deletions")    
        for line in file_deletions:
            print(line)

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

    def CalculateDLandAC(authors, org_author, dictionary):
        DL = 0
        AC = 0
        for a in authors:
            if a == org_author:
                DL = DL + dictionary[a]
            else:
                AC = AC + dictionary[a]
        return (DL, AC)

    def CalculateTruckFactor():
        print()
        print("Calculating Truck Factor for top 10 files")
        print()

        # Contains normalized DOA for each author on each file
        file_doa = []

        # Find top 10 files with most changes
        files = GetTop10Files()
        for line in files:
            print("Currently processing", line)
            
            fname = line[0]
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

                    print(variance)
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

            result = NormalizeValues(result)
            #result = StandardizeValues(result)
            
            print("Calculating DOA for file", fname)

            # Print results for top 10 files
            final_sorted_list_for_file = sorted(result, key=lambda tup: tup[1], reverse=True)[:5]
            for l in final_sorted_list_for_file:
                if l[1] > 0.75:
                    print(f"{bcolors.OKGREEN}--> {l}{bcolors.ENDC}")
                else:
                    print("-->", l)

            print()
            
            file_doa.append((fname, final_sorted_list_for_file))

        #calculate truck factor
        #iterate through authors, checking that they are 'owners' of atleast 50% of the articles
        tf = 0
        pyfiglet.print_figlet("TRUCK FACTOR")
        # this could be refined...
        print("No. of authors", all_authors.__len__())
        print("No. of files", file_doa.__len__())
        print()
        print("Author(s) with file ownership:")
        for a in all_authors:           
            count = 0
            for e in file_doa:
                for t in e[1]:
                    author = t[0]
                    normalizeddoa = t[1]
                    if author == a:
                        if normalizeddoa > 0.75:
                            count = count + 1
            if count > 0:
                print("Author", a)
                print("Owner of ", count, "files")

            if count / file_doa.__len__() > 0.5:
                tf = tf + 1
        print()
        print("The Truck Factor for this project is")
        print()
        pyfiglet.print_figlet("  //  " + str(tf) + "  //  ")
        
        if tf < 2:
            print("Your project has a low truck factor. Only a single person have to leave the project for it to be in serious danger for decay")

        print()
        print()

    # PROGRAM FLOW
    printIntro()
    #printTop10Committers(author_commit_dict)
    #printBottom10Committers(author_commit_dict)
    #FileOverview()
    CalculateTruckFactor()
    # PROGRAM END
