from flask import Flask, render_template, request, redirect, make_response, send_file, flash, Response
import json
import requests
from bs4 import BeautifulSoup
import csv
from collections import defaultdict

from io import StringIO
app = Flask(__name__)
app.secret_key = '123456'
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}

def getSoup(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup 

def getWordCount(soup):
    text = []
    tags = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p"])
    for tag in tags:
        text.append(tag.text.strip().split())
    word_count = 0
    for group in text:
        for word in group:
            word_count += 1
    return word_count

def getMetaTitle(soup):
    title = soup.find("title").text
    return title

def getHTagsNew(soup):
    text = []
    for tags in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text.append({"heading": tags.name.upper(), "text": tags.text.strip()})
    return text

@app.route('/')
def index():
    urls_data = []
    for key, value in request.cookies.items():
        if key[0:4] == "http":
            urls_data.append(json.loads(value))
    return render_template("index.html", urls_data=urls_data)

@app.route('/calculate', methods=["POST"])
def calculate():
    url = request.form["url"]
    soup = getSoup(url)
    hTags = getHTagsNew(soup)
    url_data = json.dumps({"url": url, "word count": getWordCount(soup), "meta title": getMetaTitle(soup), "headings": hTags})
    resp = make_response(redirect('/'))
    resp.set_cookie(url, url_data)
    return resp

@app.route('/export-csv', methods=['POST'])
def exportCSV():
    data = request.form.get('outlineData')
    if data:
        data = json.loads(data)
        outline_data = data.get('outline', [])
        additional_details = data.get('details', {})
        output = StringIO()
        thewriter = csv.writer(output)
        
        # Write headers for the columns
        thewriter.writerow(['Tag', 'Details'])
        
        # Write additional details first (if any)
        for detail_key, detail_value in additional_details.items():
            # Assuming additional details also follow the format "TAG:Details"
            tag, detail = detail_key.split(':', 1) if ':' in detail_key else (detail_key, detail_value)
            thewriter.writerow([tag, detail])
            
        # Now process each item in the outline data
        for item in outline_data:
            # Split the item into tag and detail by the first occurrence of ':'
            tag, detail = item.split(':', 1) if ':' in item else ('Unknown', item)
            thewriter.writerow([tag.strip(), detail.strip()])
        
        output.seek(0)
        response = Response(output.getvalue(), content_type='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=website-text-analyser.csv'
        return response
    else:
        flash('No data to export.', 'error')
        return redirect('/')

@app.route('/clearcookies', methods=['POST'])
def clearCookies():
    resp = make_response(redirect('/'))
    for key in request.cookies.keys():
        resp.delete_cookie(key)
    flash('All cookies cleared successfully!', 'success')
    return resp

@app.route('/deletecookie', methods=["POST"])
def deleteCookie():
    cookieName = request.form["url"]
    resp = make_response(redirect('/'))
    resp.set_cookie(cookieName, '', expires=0)
    return resp

if __name__ == '__main__':
    app.run(debug=False)
