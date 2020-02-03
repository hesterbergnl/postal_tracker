import tkinter as tk
import requests as rq
import bs4
import re
from selenium import webdriver

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

#Class that stores info about each package
#TODO: Make the parameters private
class Trackable:
    def __init__(self, carrier, trackingNum, origin, description):
        self.carrier = carrier
        self.trackingNum = trackingNum
        self.origin = origin
        self.description = description

#Creates a new item and prompts the user for details
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

#Tracks and USPS package and prints the details to the screen
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
        
    printPkg(newPkg, date, status)

#Tracks and prints out a UPS package
def trackUPS(newPkg):
    #This will request using selenium and save the page
    #TODO add a try catch block
    browser = webdriver.PhantomJS()
    browser.get(ups + newPkg.trackingNum)
    upsHTML = browser.page_source
    upsParser = bs4.BeautifulSoup(upsHTML, 'html.parser')

    statusTag = upsParser.select('#stApp_txtPackageStatus')
    status = statusTag[0].getText()

    date = ""

    printPkg(newPkg, date, status)


#Prints out the package details to the terminal
def printPkg(pkg, date, status):
    print("Package Arriving from: " + pkg.origin + " via " + pkg.carrier + "\n"
          "Description : " + pkg.description + "\n"
          "Tracing Number: " + pkg.trackingNum  + "\n"
          "Status: " + status + "\n"
          "Arriving on: " + date + "\n\n")


#displays all the tracked items in the list object
#TODO: throw an exception if the carrier DNE
def showItems():
    for item in trackList:
        if(item.carrier == 'USPS'):
            trackUSPS(item)
        
          
def main():
    while(1):
        option = input("Enter an option: \n 1. Status \n 2. New Track \n 3. Exit\n");
        if(option == '3'):
            break
        if(option == '2'):
            newItem()
        if(option == '1'):
            showItems()

#Call the main method on program startup
if __name__ == "__main__":
    main()
