
function createTitle(user) {

    firstName = user.name.split(' ')[0];
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


function displayGoogleUserData(user) {
    const myTable = objectToTable(user);
    document.getElementById("google-user-data").innerHTML = myTable;
}

function objectToTable(obj) {
    // Define a mapping of labels to object properties

    const labelToProperty = {
        'Vorname': 'given_name',
        'Nachname': 'family_name',
        'Email': 'email',
        'Sprache' : 'locale',
        'Profilbild' : 'picture'
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

    const full_name = user.given_name + " " + user.family_name;
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
