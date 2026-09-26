// ------------------------------------
// IMAGE BACKUP SYSTEM
// ------------------------------------

function swapImage(imageElement) {

    const backupUrl =
        imageElement.dataset.backup;


    // Check whether backup has already been tried

    if (
        backupUrl &&
        imageElement.dataset.triedBackup !== "1"
    ) {

        imageElement.dataset.triedBackup = "1";

        imageElement.src = backupUrl;

    }

    else {

        // Hide image if both URLs fail

        imageElement.style.display = "none";

    }

}


// ------------------------------------
// AUTOMATIC FLASH MESSAGE REMOVAL
// ------------------------------------

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const messages =
            document.querySelectorAll(".flash");


        setTimeout(
            function () {

                messages.forEach(
                    function (message) {

                        message.remove();

                    }
                );

            },
            4500
        );

    }
);