from os import environ


networks = {
    "development": {
        "mode": "Infura",
        "scheme": "https",
        "endpoints": "mainnet"
    }
}

infura_settings = {
    "project_id": environ["PROJECT_ID"],
    "project_secret": environ["PROJECT_SECRET"],
}
