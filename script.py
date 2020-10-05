from pydriller import RepositoryMining
from datetime import datetime
import pyfiglet
import operator
import math
import emoji
import io
from contextlib import redirect_stdout
import os

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
def run_analysis(since, to, url):

    # limit to time of writing script for reproduceable results
    commits = RepositoryMining(path_to_repo=url, since=since ,to=to)

    count = 0       # number of commits
    merges = 0      # number of merges
    all_authors = []
    author_commit_dict = dict()
    internal_authors = []
    external_authors = []
    code_changes = []
    code_files = []
    iac_changes = []
    iac_files = []
    project_name = ""

    filepath = []

    # parse commits and mine information. Runs in O(numOfCommits*CommitModifications) O(n)
    for commit in commits.traverse_commits():
        if not project_name == "":
            project_name = commit.project_name

        msg = commit.msg
        author = commit.author.email
        org_author = commit.committer.email
        count = count + 1
        
        if commit.merge:
            merges = merges + 1

        # parse files in this commit
        changedFiles = commit.modifications
        for file in changedFiles:
            filename = file.filename
            
            old = file.old_path
            new = file.new_path
            print(old)
            print(new)
            # track filepath
            if old == None:
                # file is added in this commit
                if not filepath.__contains__(new):
                    filepath.append(new)
            elif new == None:
                # deleted in this commit
                if filepath.__contains__(old):
                    filepath.remove(old)
            else:
                # file moved
                # change old_path in collection to new_path
                if filepath.__contains__(old):
                    filepath.remove(old)
                if not filepath.__contains__(new):
                    filepath.append(new)


            loc = file.nloc
            
            # check if file is in exclude list

            if not loc == None:
                # code files
                lines_added = file.added
                lines_removed = file.removed
                code_changes.append((commit.hash, author, filename, msg, lines_added, lines_removed, org_author))
                if not code_files.__contains__(filename):
                    code_files.append(filename)
            else:
                # documentation and IAC files
                lines_added = file.added
                lines_removed = file.removed
                iac_changes.append((commit.hash, author, filename, msg, lines_added, lines_removed, org_author))
                if not iac_files.__contains__(filename):
                    iac_files.append(filename)

        # Create overall collection of all authors independnt of company and count number of commits
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
    # commit parsing done

    # Prints the header information. Can be enabled/disabled in PROGRAM FLOW below
    def printIntro():
        # Print program information to user
        print()
        pyfiglet.print_figlet("VCS Analysis")
        print("by Christoffer Nissen (ChristofferNissen)")
        print()
        print()
        print("Analysing", url)
        print("Project Name:", project_name)
        print("Since:", since)
        print("To:", to)
        print("Total number of commits", count)
        print("Total number of merge commits", merges)
        print("Total number of authors", all_authors.__len__())
        print("Internal committers:", internal_authors.__len__())
        print("External committers:", external_authors.__len__())

    # Prints the Top 10 Committers. Can be enabled/disabled in PROGRAM FLOW below
    def printTop10Committers(collection):
        print()
        print("Top committers")
        top10commiters = sorted(collection, key=collection.get, reverse=True)[:10]
        i = 1
        for tc in top10commiters:
            print("[",i,"]", "Email:", tc, "Count:", collection[tc], "Total %", collection[tc]/count*100)
            i = i + 1

    # Prints the Bottom 10 Committers. Can be enabled/disabled in PROGRAM FLOW below
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
    
    def GetFiles():
        result = []
        for line in CreateMapOfCommitAdditionsAndDeletesPerFileName():
            result.append((line[0], line[1]+line[2]))
        return sorted(result, key=lambda tup: tup[1], reverse=True)#[:10]

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
        files = GetFiles()
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

            # calculate DOA for each contributer
            author_doa = []
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

                author_doa.append((a, doa))

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

            author_doa_normalized = NormalizeValues(author_doa)
            #result = StandardizeValues(result)
            
            print("Calculating DOA for file", fname)

            # Print results for top 10 files
            author_doa_normalized_sorted_topfive = sorted(author_doa_normalized, key=lambda tup: tup[1], reverse=True)[:5]
            for l in author_doa_normalized_sorted_topfive:
                if l[1] > 0.75:
                    print(f"{bcolors.OKGREEN}--> {l}{bcolors.ENDC}")
                else:
                    print("-->", l)

            print()
            
            file_doa.append((fname, author_doa_normalized_sorted_topfive))

        #calculate truck factor
        #iterate through authors, checking that they are 'owners' of atleast 50% of the articles
        pyfiglet.print_figlet("TRUCK FACTOR")
        fileWithFileAuthor = []
        fileAuthors = []
        filesWithAuthors = []
        authorAndCount = []
        print("No. of files", file_doa.__len__())
        print("No. of code files", code_files.__len__())
        print("No. of (excluded) iac files", iac_files.__len__())
        print("No. of authors", all_authors.__len__())
        for a in all_authors:           
            count = 0
            for e in file_doa:
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

        authorAndCount = sorted(authorAndCount, key=lambda tup: tup[1], reverse=True)
        print("No. of authors with ownership", fileAuthors.__len__())

        print()
        print("Author(s) with file ownership:")
        totalCount = 0
        for t in authorAndCount:
            a = t[0]
            count = t[1]
            totalCount = totalCount + count
            if count > 0:
                print("Author", a)
                print("Owner of ", count, "files")

        # Check that 0.5 of files have an author
        # Loop over files and count each time a file has an author
        # we have a touple of (file, author) for each ownership
        tf = 0
        for t_ac in authorAndCount:
            a = t_ac[0]
            c = t_ac[1]
            
            # count unique files with authors
            uq = 0
            seenFiles = []
            for t in fileWithFileAuthor:
                f = t[0]
                if not seenFiles.__contains__(f):
                    seenFiles.append(f)
                    uq = uq + 1

            ratio = uq / file_doa.__len__()

            if ratio > 0.5:
                tf = tf + 1 
                # remove author tuples
                tmp = []
                for v in fileWithFileAuthor:
                    author = v[1]
                    if not author == a:
                        tmp.append(v)
                fileWithFileAuthor = tmp
            else:
                break

        print()
        print("The Truck Factor for this project is")
        print()
        pyfiglet.print_figlet("  //  " + str(tf) + "  //  ")
        
        if tf < 2:
            print("Your project has a low truck factor. Only a single person have to leave the project for it to be in serious danger due to lack of maintainers")

        print()

    # PROGRAM FLOW
    printIntro()
    printTop10Committers(author_commit_dict)
    #printBottom10Committers(author_commit_dict)
    FileOverview()
    CalculateTruckFactor()
    # PROGRAM END



urls = [
        "https://github.com/Praqma/helmsman",
        # "https://github.com/rabbitmq/rabbitmq-server",
        # "https://github.com/docker/docker-ce",
        # "https://github.com/docker/cli",
        # "https://github.com/jenkinsci/jenkins",
        # "https://github.com/prometheus/prometheus",
        # "https://github.com/grafana/grafana",
        # "https://github.com/apache/kafka",
        # "https://github.com/kubernetes/ingress-nginx",
        # "https://github.com/kubernetes/kubernetes",
        # "https://github.com/golang/go",
        # #"https://github.com/torvalds/linux",
        # "https://github.com/microsoft/vscode",
        # "https://github.com/ohmyzsh/ohmyzsh",
        # "https://github.com/tensorflow/tensorflow",
        # "https://github.com/puppetlabs/puppet/"
        ]
since = None
#to = datetime(2016, 4, 22, 0, 0)
to = datetime(2020, 9, 28, 0, 0)

# for url in urls:
#     f = io.StringIO()
#     with redirect_stdout(f):
#         run_analysis(since, to, url)
        
#     out = f.getvalue()
#     arr = url.split("/")
#     projectName = arr[arr.__len__()-1]
#     fileName = "paper_results/"+projectName+".txt"
#     f = open(fileName, "w")
#     f.write(out)
#     f.close()
#     print(out)

# test
def expandExcludeList(url, excludePaths):
    finalExcludeList = []
    for ep in excludePaths:
        uniquePaths = []
        # needs input in 'as of current commit'
        for commit in RepositoryMining(url, filepath=ep).traverse_commits():
            filesChanged = commit.modifications
            
            for f in filesChanged:

                path = ""
                if f.new_path == None:
                    # deleted file
                    #print("deleted", f.old_path)
                    path = f.old_path
                elif f.old_path == None:
                    # new file
                    #print("created", f.new_path)
                    path = f.new_path
                elif f.new_path == f.old_path:
                    #print("updated", f.new_path)
                    path = f.new_path

                if ep in path:
                    # old = f.old_path
                    # new = f.new_path
                    # print("old", old)
                    # print("new", new)
                    if not uniquePaths.__contains__(path):
                        uniquePaths.append(path)

        for p in uniquePaths:
            # extract filename
            arr = p.split("/")
            filename = arr[arr.__len__()-1]

            for commit in RepositoryMining(url, filepath=p).traverse_commits():
                filesChanged = commit.modifications
                for f in filesChanged:

                    if f.new_path == None:
                        # deleted file
                        #print("deleted", f.old_path)
                        path = f.old_path
                    elif f.old_path == None:
                        # new file
                        #print("created", f.new_path)
                        path = f.new_path
                    elif f.new_path == f.old_path:
                        #print("updated", f.new_path)
                        path = f.new_path
                    
                    if filename in path:
                        if path not in finalExcludeList:
                            finalExcludeList.append(path)
    return finalExcludeList

url = "https://github.com/Praqma/helmsman"
exclude = ["internal/app/"]
tmp = expandExcludeList(url, exclude)
for v in tmp:
    print(v)

