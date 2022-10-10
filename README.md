
# Immoscout monitor

 Immoscout24 monitor which monitors new properties and send a message with discord webhooks. Uses no proxies.

## Installation guide
1. Install all dependencies from requirments.txt
2. Create a mongodb Database. (Recommended: MongoDB Atlas)
3. Create a discord server with a webhook
4. Get your immoscout24 search link
5. Edit config.py
6. Run the script


## Get your immoscout search link
1. Open https://www.immoscout24.ch/en and filter for your new propertie.
2. Press F12 to get into the developer tools
3. Switch to network tab
4. Press "search" and look up the request with /properties.
5. Save the link and past it into config.py