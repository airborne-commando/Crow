# Crow
A gui Edition of the OSINT tool blackbird.

To install simply clone [blackbirds repo](https://github.com/p1ngul1n0/blackbird.git) from here you may install crow by [cloning it](https://github.com/airborne-commando/crow) or downloading the files from this repo and placing them inside blackbirds root directory.

In one command:

    git clone https://github.com/p1ngul1n0/blackbird.git && git clone https://github.com/Nthompson096/crow.git && mv crow/*.txt ./blackbird/ && mv crow/*.py ./blackbird/ && cd ./blackbird/ && python3 -m venv venv && source venv/bin/activate && pip3 install -r requirements.txt && pip3 install -r requirements_GUI.txt

after that's finished feel free to run:

    python3 crow.py

# Features

Hudson email search:
* Search an email for hudson rock to see if it's been assocated with an infected computer.

![image](https://github.com/user-attachments/assets/9685a7a4-50b1-4032-8e0c-67cb2ef3631b)

* Save and search functions to continue an OSINT in JSON formatting

![image](https://github.com/user-attachments/assets/25551407-b006-439d-8d7a-c586f1740986)

* contents of the saved json file, example:

        {
            "hudson_email_input": "",
            "username_input": "manvirdi2000",
            "email_input": "manvirdi2000@gmail.com",
            "permute_checkbox": true,
            "permuteall_checkbox": true,
            "no_nsfw_checkbox": true,
            "proxy_input": "127.0.0.1",
            "timeout_spinbox": 30,
            "no_update_checkbox": true,
            "csv_checkbox": true,
            "pdf_checkbox": true,
            "verbose_checkbox": true,
            "dump_checkbox": true,
            "instagram_session_id": "",
            "AI_checkbox": true,
            "filter": "cat=social"
        }

As for the instagram session ID; I'd probably recommend using a fake instagram account if you can that way you don't get locked out of your main. However you may be already aware of that.
