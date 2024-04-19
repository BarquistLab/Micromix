def main(parameters):
    upload_url = "http://127.0.0.1:8081/"
    print("heatmap.py")
    print(parameters)
    return upload_url+'?config='+str(parameters["db_entry_id"])
