'''
Postal Tracker
@author Nikolai Hesterberg
'''
import tkinter as tk
import requests as rq
import time
import bs4
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

#  https://stackoverflow.com/questions/53657215/running-selenium-with-headless-chrome-webdriver
# These options are used to run chrome headless (no gui) and with less overhead
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")

#The following are the first part of the tracking URL for the major carriers
usps = 'https://tools.usps.com/go/TrackConfirmAction?tLabels='
fedex = 'https://www.fedex.com/apps/fedextrack/?tracknumbers='
ups = 'https://www.ups.com/track?loc=en_US&tracknum='

#These headers will stop the redirection loop
headers = {
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
}

#Save the tracking items in a list
trackList = []


"""
Trackable class - class that stores all details of a trackable package

@author Nikolai Hesterberg

TODO: Make the parameters private, add getters and setters 
"""
class Trackable:
    """
    Constructor to build a trackable object

    @param carrier - the carrier of the package, USPS, Fedex, or UPS supported
    @param trackingNum - the tracking number of the package
    @param origin - origin of the package - who shipped it
    @param description - description of the package - what it contains
    """
    def __init__(self, carrier, trackingNum, origin, description):
        self.carrier = carrier
        self.trackingNum = trackingNum
        self.origin = origin
        self.description = description

    """
    Status and Date of the packages.  Store the current status and expected delivery for caching
    """
    status = ""
    date = ""


"""
Creates a new package to track
Prompts the user for package information and calls the relevant tracking method depending on the carrier
"""
def newItem():
    carrier = input("Enter the carrier: \n 1. USPS \n 2. Fedex \n 3. UPS \n")
    trackingNum = input("Enter the tracking number: ")
    origin = input("Enter the shipper: ")
    description = input("Enter a description: ")
    print("\n")
    
    if(carrier == '1'):
        newPkg = Trackable("USPS", trackingNum, origin, description)
        trackList.append(newPkg)
        trackUSPS(newPkg)
    elif(carrier == '2'):
        newPkg = Trackable("Fedex", trackingNum, origin, description)
        trackList.append(newPkg)
        trackFedex(newPkg)
    elif(carrier == '3'):
        newPkg = Trackable("UPS", trackingNum, origin, description)
        trackList.append(newPkg)
        trackUPS(newPkg)
    else:
        return

"""
Tracks USPS packages and then calls the print method to display the results

Uses the requests python package to download the html file for the tracking page
Doesn't use selenium because requests is faster, but it may need selenium in the future

Parses the HTML file using BeautifulSoup
"""
def trackUSPS(newPkg):
    regexPat = "(\n)(.*)(\n\n)"
    
    #This will request and save the page... but should add a try/catch block
    uspsHTML = rq.get(usps + newPkg.trackingNum, headers=headers)
    uspsHTML.raise_for_status()
    uspsParser = bs4.BeautifulSoup(uspsHTML.text, 'html.parser')

    statusTag = uspsParser.select('.delivery_status > h2:nth-child(2) > strong:nth-child(1)')
    status = statusTag[0].getText()

    date = ""

    #If the item is delivered, it will not longer have an expected delivery day
    if(status.lower() != 'delivered'):
        dateTag = uspsParser.select('.date')
        print(dateTag)
        day = dateTag[0].get_text()

        monthYearTag = uspsParser.select('.month_year')
        monthYearFull = monthYearTag[0].get_text()
        
        monthYear = re.search(regexPat, monthYearFull).group(2)
        date = day + " " + monthYear

    newPkg.date = date
    newPkg.status = status
    
    printPkg(newPkg)

"""
Tracks UPS packages and then calls the print method to display the results

Uses the selenium python package and chromedriver to save the webpage.
Requires selenium for javascript generation.

Parses the HTML file using BeautifulSoup
"""
def trackUPS(newPkg):
    #This will request using selenium and save the page
    #TODO add a try catch block
    browser = webdriver.Chrome(options=chrome_options)
    browser.get(ups + newPkg.trackingNum)
    upsHTML = browser.page_source
    browser.close()
    
    upsParser = bs4.BeautifulSoup(upsHTML, 'html.parser')

    statusTag = upsParser.select('#stApp_txtPackageStatus')
    status = statusTag[0].getText()

    date = ""

    newPkg.date = date
    newPkg.status = status
    
    printPkg(newPkg)

#Tracks and prints out a fedex package
def trackFedex(newPkg):
    #This will request using selenium and save the page
    #TODO add a try catch block
    browser = webdriver.Chrome(options=chrome_options)
    browser.get(fedex + newPkg.trackingNum)
    #page is slow to load, so need to wait for it to fully load
    time.sleep(3)
    fedexHTML = browser.page_source
    browser.close()
    
    fedexParser = bs4.BeautifulSoup(fedexHTML, 'html.parser')
    
    statusTag = fedexParser.select('h3.redesignStatusChevronTVC:nth-child(2)')
    status = statusTag[0].getText()
    
    date = ""
    
    if(status.lower() == 'in transit'):
        dateTag = fedexParser.select('.snapshotController_date')
        date = dateTag[0].getText()

    newPkg.date = date
    newPkg.status = status
    
    printPkg(newPkg)

#Prints out the package details to the terminal
def printPkg(pkg):
    print("Package Arriving from: " + pkg.origin + " via " + pkg.carrier + "\n"
          "Description : " + pkg.description + "\n"
          "Tracing Number: " + pkg.trackingNum  + "\n"
          "Status: " + pkg.status + "\n"
          "Arriving on: " + pkg.date + "\n\n")


#prints all the tracked items in the list object
def showItems():
    for item in trackList:
        printPkg(item)
        

#updates all of the saved tracking information
#TODO: Parallelize the tracking if there are a lot of items
def updateItems():
    for item in trackList:
        if(item.carrier == 'USPS'):
            trackUSPS(item)
        if(item.carrier == 'Fedex'):
            trackFedex(item)
        if(item.carrier == 'UPS'):
            trackUPS(item)








#Main method - loops the main menu and waits for user input
def main():
    while(1):
        option = input("Enter an option: \n 1. Status \n 2. New Track \n 3. Update \n 4. Exit\n");
        if(option == '4'):
            break
        if(option == '3'):
            updateItems()
        if(option == '2'):
            newItem()
        if(option == '1'):
            showItems()

#Call the main method on program startup
if __name__ == "__main__":
    main()
