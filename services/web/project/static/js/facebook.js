let myPieChart = null; //define chart variable globally

// This is called with the results from FB.getLoginStatus().
function statusChangeCallback(response) {
    console.log('statusChangeCallback');
    console.log(response);
    if (response.status === 'connected') {
        loadFacebookData();
    } else {
         document.getElementById('status').innerHTML = 'Please log into this webpage.';
    }
}

// Called when a person is finished with the Login Button.
function checkLoginState() {
   FB.getLoginStatus(function(response) {
        statusChangeCallback(response);
    });
}

                        // Initialize the JavaScript SDK
window.fbAsyncInit = function() {
   FB.init({
    appId      : '184791784339843',
    cookie     : true,
    xfbml      : true,
    version    : 'v16.0'
});
};

// Load the SDK asynchronously
(function(d, s, id){
var js, fjs = d.getElementsByTagName(s)[0];
if (d.getElementById(id)) {return;}
js = d.createElement(s); js.id = id;
js.src = "https://connect.facebook.net/en_US/sdk.js";
fjs.parentNode.insertBefore(js, fjs);
}(document, 'script', 'facebook-jssdk'));

function loadFacebookData() {
    // Fetch user info
    FB.api('/me', {fields: 'name,first_name,middle_name,last_name,short_name,email,birthday,age_range,gender,hometown,location'}, function(response) {
        // Process user info
        processUserData(response);
    });


    FB.api('/me/posts', 'GET', {fields:"id,privacy,message,multi_share_optimized,name,link,created_time"},
    function(response) {
        if (response && response.data) {
            displayFacebookPostData(response);
        } else {
            console.error('Error fetching posts:', response.error);
        }
    });

}


function processUserData(response) {
    fetch('/process_facebook_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(response)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.href = "/login_successful";
        } else {
            console.error("Error in processing Facebook data.");
        }
    })
    .catch(error => {
        console.error('There has been a problem with your fetch operation:', error);
    });
}

function processPostData(postResponse) {
    console.log(postResponse);
    displayFacebookPostData(postResponse);
}

const columnHeaderMap = {
    'privacy': 'Who can see my posts?',
    'link': 'Link',
    'created_time': 'Created Time'
};

function displayFacebookPostData(posts) {
    let postsArray = [];
    posts.data.forEach((post) => {
        let postObj = {
            privacy: post.privacy.value,
            link: post.link,
            created_time: post.created_time
        }
        postsArray.push(postObj)
    });

    const myTable = objectArrayToTable(postsArray);

    document.getElementById("facebook-post-data").innerHTML = myTable;

}

function objectArrayToTable(array) {
    let table = "<table align=center class='styled-table'>";
    let first = true;

    array.forEach((obj) => {

        let privacyClass = obj.privacy.toLowerCase().replace(/[^a-z0-9]/g, '-');

        if (first) {
            table += "<tr>"
            for (let prop in obj) {
                table += `<th>${columnHeaderMap[prop] || prop}</th>`;
            }
            table += "</tr>"
            first = false;
        }

        table += `<tr class="${privacyClass}">`;
        for (let prop in obj) {
            table += "<td>" + obj[prop] + "</td>";
        }
        table += "</tr>"
    });

    table += "</table>";
    return table;
}


function createTitle(user) {
    firstName = user.first_name;
    firstName = firstName + "!";
    document.getElementById("userFirstName").textContent = firstName;
}

function getUserIP(user) {
    ip = user.user_ip
    ip_details = user.ip_details
    document.getElementById("userIP").innerHTML = ip;
    ip_location = ip_details.city + ", " + ip_details.country
    document.getElementById("ipInfo").innerHTML = ip_location;
    console.log(ip_location)
}

function displayFacebookUserData(user) {
    const myTable = objectToTable(user);
    document.getElementById("facebook-user-data").innerHTML = myTable;
}

function objectToTable(obj) {
    // Define a mapping of labels to object properties

    const labelToProperty = {
        'Vorname': 'first_name',
        'Nachname': 'last_name',
        'Email': 'email',
    };

    let table = "<table align=center class='styled-table table-responsive border-0'>";
    for (let label in labelToProperty) {
        const property = labelToProperty[label];
        table += "<tr><td style='font-weight:bold'>" + label + "</td><td>" + obj[property] + "</td></tr>";
    }
    table += "</table>";
    return table;
}


function google_dorks(user) {

    const full_name = user.first_name + " " + user.last_name;
    const dork1 = "\"" + full_name + "\"" + " -filetype:pdf";

    // Construct Google search URL with the dork
    const googleSearchURL1 = "https://www.google.com/search?q=" + encodeURIComponent(dork1);

    // Update the innerHTML with an anchor tag
    document.getElementById("generatedLink1").innerHTML = `<a href="${googleSearchURL1}" target="_blank">${dork1}</a>`;


    // Second generated dork
    const dork2 = "\"" + full_name + "\"" + " -filetype:pdf OR -filetype:docx";
    const googleSearchURL2 = "https://www.google.com/search?q=" + encodeURIComponent(dork2);
    document.getElementById("generatedLink2").innerHTML = `<a href="${googleSearchURL2}" target="_blank">${dork2}</a>`;

    // Third generated dork
    const dork3 = full_name + " site:instagram.com";
    const googleSearchURL3 = "https://www.google.com/search?q=" + encodeURIComponent(dork3);
    document.getElementById("generatedLink3").innerHTML = `<a href="${googleSearchURL3}" target="_blank">${dork3}</a>`;


}


function fetchAllLinks() {
    $.ajax({
        url: '/get_all_links',
        type: 'GET',
        cache: false,
        success: function(response) {
            if (response.message === 'Data not ready') {
                console.log('Data not ready yet. Retrying...');
                setTimeout(fetchAllLinks, 5000); // Retry after a delay
                return;
            }

            // Update page with all the links if available
            updateLinksOnPage(response);
        },
        error: function(error) {
            console.error('Error fetching data:', error);
            setTimeout(fetchAllLinks, 5000); // Retry after a delay
        },
        timeout: 30000 // Long poll timeout
    });
}

function updateLinksOnPage(data) {

    let postUrls = [];

    // Function to process and display links
    function displayLinks(links, containerId, infoText, iconClass) {
        if (links && links.length > 0) {
            const iconHtml = `<i class='fa-brands ${iconClass}'></i>`;
            const linksHtml = links.map(link => {
                // Check if link contains '/post/' and add to postUrls array
                if (link.match(/\/post/)) {
                    postUrls.push(link);
                }
                return `<a href="${link}">${iconHtml} ${link}</a>`;
            }).join('<br>');
            $(`#${containerId}`).html(infoText + linksHtml);
        } else {
            $(`#${containerId}`).hide();
        }
    }

    // Process Instagram links
    displayLinks(data.instagram, 'instagram-links', "<p>Es wurden potentielle Instagramprofile von dir gefunden: </p>", 'fa-instagram');

    // Process LinkedIn links
    displayLinks(data.linkedin, 'linkedin-links', "<p>Es wurden potentielle LinkedIn Profile von dir gefunden: </p>", 'fa-linkedin');

    // Process Reddit links
    displayLinks(data.reddit, 'reddit-links', "<p>Es wurden potentielle Redditprofile von dir gefunden: </p>", 'fa-reddit');

    // Process Facebook links
    displayLinks(data.facebook, 'facebook-links', "<p>Es wurden potentielle Facebookprofile von dir gefunden: </p>", 'fa-facebook');

    // Process Twitter links
    displayLinks(data.twitter, 'twitter-links', "<p>Es wurden potentielle Twitterprofile von dir gefunden: </p>", 'fa-twitter');

    // Process TikTok links
    displayLinks(data.tiktok, 'tiktok-links', "<p>Es wurden potentielle Tik-Tok Profile von dir gefunden: </p>", 'fa-tiktok');

    //Sherlock accounts
    if (data.possible_accounts) {
        let linksHtml = '';

        for (const [username, sites] of Object.entries(data.possible_accounts)) {
            let accountHtml = `<div class="account-item border-0"><h3>${username}</h3>`;

            for (const [site, url] of Object.entries(sites)) {
                accountHtml += `<a href="${url}">${url}</a><br>`;
            }

            accountHtml += '</div>';
            linksHtml += accountHtml;
        }

        $('#possible-accounts').html(linksHtml);

    }

    // Process other links
    if (data.other_links && data.other_links.length > 0) {
        const otherLinksHtml = data.other_links.map(link => `<a href="${link}">${link}</a>`).join('<br>');
        $('#other-links').html("<p>Hier findest du weitere Ergebnisse: </p>" + otherLinksHtml);
    }

    // Display post URLs in a separate div
    if (postUrls.length > 0) {
        console.log("Post URLs to display:", postUrls); // Debug log
        const postLinksHtml = postUrls.map(url => `<a href="${url}">${url}</a>`).join('<br>');
        $('#privacy').html("<p>Beiträge, die wir gefunden haben:</p>" + postLinksHtml);
    } else {
        console.log("No post URLs found"); // Debug log
    }

    // Hide spinners
    $('#spinner').hide();
    $('#spinner2').hide();
    $('#spinner3').hide();

}