from Bio import Entrez
import csv
import os


def search(query, number_of_results):
    Entrez.email = 'georgiamay.green@hotmail.co.uk'
    handle = Entrez.esearch(db='pubmed',
                            sort='relevance',
                            retmax=str(number_of_results),
                            retmode='xml',
                            term=query)
    search_results = Entrez.read(handle)
    return search_results


def fetch_details(list_of_ids):
    ids = ','.join(list_of_ids)
    Entrez.email = 'georgiamay.green@hotmail.co.uk'
    handle = Entrez.efetch(db='pubmed',
                           retmode='xml',
                           id=ids)
    query_results = Entrez.read(handle)
    return query_results


def pubmed_search(search_query: str, location: str, number_of_results: int):
    if not search_query:
        print("Please enter a search query.")
    else:
        if location:
            print("Searching PubMed for papers about {} near {}...".format(search_query.upper(), location.upper()))
        else:
            print("Searching PubMed for papers about {} in any location...".format(search_query.upper()))
        print()
        results = search(search_query, number_of_results)
        id_list = results["IdList"]
        papers = fetch_details(id_list)
        return_list = []
        if not location:
            for i, paper in enumerate(papers['PubmedArticle']):
                paper_data = {}
                print("Paper title: %s" % (paper['MedlineCitation']['Article']['ArticleTitle']))
                paper_data["title"] = paper['MedlineCitation']['Article']['ArticleTitle']
                paper_data["authors"] = []
                emails_found = False
                try:
                    testing = paper['MedlineCitation']['Article']['AuthorList']
                except KeyError:
                    continue
                for j in range(len(testing)):
                    email = None
                    author_reference = None
                    if len(paper['MedlineCitation']['Article']['AuthorList'][j]['AffiliationInfo']) != 0:
                        affiliation = paper['MedlineCitation']['Article']['AuthorList'][j]['AffiliationInfo'][0][
                            'Affiliation']
                        split_affiliation = paper['MedlineCitation']['Article']['AuthorList'][j]['AffiliationInfo'][0][
                            'Affiliation'].split()
                        for word in split_affiliation:
                            if "@" in word:
                                email = word
                                if email.endswith("."):
                                    email = email[:-1]
                                author_reference = affiliation
                                emails_found = True
                        if email:
                            try:
                                firstname = paper['MedlineCitation']['Article']['AuthorList'][j]['ForeName']
                                lastname = paper['MedlineCitation']['Article']['AuthorList'][j]['LastName']
                                print("Author name: {} {}".format(firstname, lastname))
                            except KeyError:
                                firstname = "unknown"
                                lastname = "unknown"
                                print('Author name could not be found')
                            print("Author email: {}".format(email))
                            print("Author reference: {}".format(author_reference))
                            paper_data["authors"].append(
                                {"first": firstname,
                                 "last": lastname,
                                 "email": email,
                                 "reference": author_reference}
                            )
                return_list.append(paper_data)
                if not emails_found:
                    print("No email addresses associated with this paper.")
                print()
        if location:
            for i, paper in enumerate(papers['PubmedArticle']):
                paper_data = {}
                relevant_emails_found = False
                paper_title = False
                paper_data["title"] = paper['MedlineCitation']['Article']['ArticleTitle']
                paper_data["authors"] = []
                try:
                    testing = paper['MedlineCitation']['Article']['AuthorList']
                except KeyError:
                    continue
                for j in range(len(testing)):
                    email = None
                    author_reference = None
                    if len(paper['MedlineCitation']['Article']['AuthorList'][j]['AffiliationInfo']) != 0:
                        affiliation = paper['MedlineCitation']['Article']['AuthorList'][j]['AffiliationInfo'][0][
                            'Affiliation']
                        split_affiliation = affiliation.split()
                        if location.lower() in affiliation.lower():
                            if not paper_title:
                                print("Paper title: %s" % (paper['MedlineCitation']['Article']['ArticleTitle']))
                                paper_title = True
                            for word in split_affiliation:
                                if "@" in word:
                                    email = word
                                    if email.endswith("."):
                                        email = email[:-1]
                                    author_reference = affiliation
                                    relevant_emails_found = True
                            if email:
                                try:
                                    firstname = paper['MedlineCitation']['Article']['AuthorList'][j]['ForeName']
                                    lastname = paper['MedlineCitation']['Article']['AuthorList'][j]['LastName']
                                    print("Author name: {} {}".format(firstname, lastname))
                                except KeyError:
                                    firstname = "unknown"
                                    lastname = "unknown"
                                    print('Author name could not be found')
                                print("Author email: {}".format(email))
                                print("Author reference: {}".format(author_reference))
                                paper_data["authors"].append(
                                    {"first": firstname,
                                     "last": lastname,
                                     "email": email,
                                     "reference": author_reference}
                                )
                return_list.append(paper_data)
                if not relevant_emails_found and paper_title:
                    print("No email addresses associated with this paper.")
                if paper_title:
                    print()
        print("Search complete.")
        print()
        return return_list


def scrape_pubmed(query_list):
    current_query = ""
    current_location = ""
    with open(query_list, 'r') as list_of_queries:
        with open("pubmed_emails.csv", "w") as output:
            writer = csv.writer(output)
            writer.writerow(["pubmed query",
                             "location filter",
                             "paper title",
                             "author first name",
                             "author last name",
                             "author email",
                             "author reference"])
            queries = list_of_queries.readlines()
            last = queries[-1]
            for line in queries:
                if line != last and line != "\n":
                    if not current_query:
                        current_query = line[:-1]
                    else:
                        current_location = line[:-1]
                else:
                    if line == last:
                        if current_query:
                            current_location = line
                        else:
                            current_query = line
                    results_list = pubmed_search(current_query, current_location, 1000)
                    for paper_info in results_list:
                        for author in paper_info["authors"]:
                            add_to_file = [
                                current_query,
                                current_location,
                                paper_info["title"],
                                author["first"],
                                author["last"],
                                author["email"],
                                author["reference"]]
                            try:
                                writer.writerow(add_to_file)
                            except UnicodeEncodeError:
                                continue
                    current_query = ""
                    current_location = ""
    print("ALL SEARCHES COMPLETE")
    output_location = os.path.join(os.getcwd(), "pubmed_emails.csv")
    print("Results written to {}".format(output_location))


def main():
    scrape_pubmed("queries.txt")


if __name__ == "__main__":
    main()
