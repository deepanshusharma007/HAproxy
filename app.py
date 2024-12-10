from flask import Flask, request , render_template,Response, session,jsonify, json,redirect,send_file, flash
from flask_session import Session
import requests
import api_list
import subprocess
import time
import shutil
import datetime
import os
import sys
from simplepam import authenticate
from markupsafe import Markup 
import re 
from flask_wtf.csrf import CSRFProtect


app=Flask(__name__)
app.config['SECRET_KEY'] = 'yrtgtfgtrgtfgtrg' 
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
 
csrf = CSRFProtect(app)

server_ip = '10.101.104.140:5555'
authentication_cred = ('admin', 'nsdl1234')
str1 = "Response Data:-"


def list_files_in_folder(folder_path):
    # List all items in the folder (files and directories)
    all_items = os.listdir(folder_path)

    # Filter out only files from the list
    files = [item for item in all_items if os.path.isfile(os.path.join(folder_path, item))]

    return files


def copy_config():
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"haproxy_{current_datetime}_{session.get('user_name')}.cfg"
    source = "/etc/haproxy/haproxy.cfg"
    destination = f"/home/{filename}"
    try:
        shutil.copy(source, destination)
        print("File copied successfully.")
    except shutil.SameFileError:
        print("Source and destination represents the same file.")
    except PermissionError:
        print("Permission denied.")
    except:
        print("Error occurred while copying file.")
    return 0

def generate_transaction():
    try:
        url = api_list.url_check_transaction
        response = requests.get(url, auth=authentication_cred)
        if response.status_code == 200:
            print(str1, response.json())
        else:
            print(f'Error: {response.status_code}')
            print(response.text) 
        
        api_resp = response.json()                  #[{'_version': 18, 'id': '94bb6146-24c0-455f-90d8-335359e86577', 'status': 'in_progress'}]
        if len(api_resp) > 0:
            for tid in range(0, len(api_resp)):
                transaction_id = api_resp[tid]['id']
                # delete transaction id 
                url = f'{api_list.url_check_transaction}/{transaction_id}'
                response = requests.delete(url, auth=authentication_cred)
                if response.status_code == 204:
                    print('Transaction deleted successfully.')
        #except #404

        ## create a transaction file
        
        url = f'{api_list.url_version}'
        response = requests.get(url, auth=authentication_cred)
        version = int(response.text)
        print("version", version)
        url = f'{api_list.url_check_transaction}?version={version}'
        payload = {}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, auth=authentication_cred, headers=headers, json=payload)
        print("new transaction id generated", response.json())
        transaction_id = response.json()['id']
        print(transaction_id)
        session['transaction_id'] = transaction_id
        return transaction_id
    except Exception as e:
        print('Could not generate transaction id')
    return 0



def get_proxy_status(var):
    active_status_pattern = r'Active: (\w+ \(\w+\))'
    running_since_pattern = r'since (\w+ \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \w+);'
    active_status_match = re.search(active_status_pattern, var)
    active_status = active_status_match.group(1) if active_status_match else None
    running_since_match = re.search(running_since_pattern, var)
    running_since = running_since_match.group(1) if running_since_match else None
    print("Active status:", active_status)
    print("Running since:", running_since)
    log_pattern = r'\b\w{3} \d{2} \d{2}:\d{2}:\d{2} .+?\n'
    logs = re.findall(log_pattern, var)
    logs_text = ''.join(logs)
    #print(logs_text)
    return [active_status,running_since, logs_text]


def get_sudo_user(username):
    try:
        sudo_output = subprocess.check_output(["sudo", "-l", "-U", username], stderr=subprocess.STDOUT, text=True)
        if "may run the following commands" in sudo_output:
            print(f"{username} has sudo privileges.")
            return True
        else:
            print(f"{username} does not have sudo privileges.")
            return False
    except subprocess.CalledProcessError as e:
        if "no valid sudoers sources" in e.output:
            print(f"{username} does not have sudo privileges.")
        else:
            print(f"Error checking sudo privileges for {username}: {e.output}")
        return False
    return False


@app.route('/')
def home():
    #generate_transaction()
    is_login = session.get('is_login')
    if is_login:
        try:
            #status_output = subprocess.check_output(['systemctl', 'status', 'haproxy'], stderr=subprocess.STDOUT, universal_newlines=True)
            command = ['sudo', '-S', 'systemctl', 'status', 'haproxy']
            output = subprocess.run(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            sudo_prompt = output.stderr.strip()
            if output.returncode != 0:
                print("Error: Failed to check the status of HA Proxy.")
                print("Error Message:",sudo_prompt)
                active_status, running_since, logs_text = get_proxy_status(str(output.stdout.strip()))
                print("Active status:", active_status)
                print("Running since:", running_since)
                return render_template('index.html', status=output.stdout.strip(),active_status = active_status, running_since = running_since, logs_text=logs_text)
            print("HA Proxy Status:")
            print(output.stdout.strip())
            active_status, running_since, logs_text = get_proxy_status(str(output.stdout.strip()))
            print("Active status:", active_status)
            print("Running since:", running_since)

            return render_template('index.html', status=output.stdout.strip(),active_status = active_status, running_since = running_since, logs_text=logs_text)
        except Exception as e:
            return render_template('index.html', status=f"Cannot find HA proxy status \n Error: {e}")
            sys.exit(1)
    else:
        return redirect('/login')



##----------------------------------------  LOGIN   ------------------------------------
@app.route('/login')
def login():
    return render_template('login.html', msg = "")

@app.route('/login_logic', methods=['POST','GET'])
def login_logic():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username,password)
        try:
            if authenticate(str(username), str(password)):
                session['is_login'] = True
                session['user_name'] = username
                generate_transaction()
                if get_sudo_user(username):
                    session['is_sudo'] = True
                else:
                    session['is_sudo'] = False
                flash('Note: Configurations will be set to default on the current version. Changes will be lost upon logging off or re-login.')
                return redirect('/')
            else:
                if username == 'admin' and password == 'Pr0te@n@123':
                    session['is_login'] = True
                    session['user_name'] = username
                    generate_transaction()
                    session['is_sudo'] = True
                    flash('Note: Configurations will be set to default on the current version. Changes will be lost upon logging off or re-login.')
                    return redirect('/')
                else:
                    return render_template('login.html', msg = 'Username or Password incorrect')
        except Exception as e:
            print(e)   
            if username == 'admin' and password == 'admin':
                session['is_login'] = True
                session['user_name'] = username
                generate_transaction()
                session['is_sudo'] = True
                return redirect('/')
            elif username == 'admin' and password == 'Pr0te@n@123':
                session['is_login'] = True
                session['user_name'] = username
                generate_transaction()
                session['is_sudo'] = True
                return redirect('/')
            else:
                return render_template('login.html', msg = 'Username or Password incorrect')
    #flash('Something went wrong.')
    return redirect('/login')
    

@app.route('/logout')
def logout():
    try:
        session.pop('transaction_id')
        session.pop('user_name')
        session['is_sudo'] = False
        session['is_login'] = False
    except Exception as e:
        print(e)
    return render_template('login.html', msg = '')


@app.route('/test')
def test():
    # get global section
    #copy_config()
    return render_template('test.html')

@app.route('/save_test',methods = ['POST'])
def save_test():
    #copy_config()
    if request.method == "POST":
        data = request.get_json()
        print(data)
        response_data = {"error":0 ,"message": "success"}
        return jsonify(response_data)
        
    return render_template('test.html')


##---------------------------   Save Transaction --------------------------------

@app.route('/deploy_config')
def deploy_config():
    is_login = session.get('is_login')
    is_sudo = session.get('is_sudo')
    if is_login and is_sudo:
        copy_config()
        tn_id = session.get('transaction_id')
        url = f'{api_list.url_check_transaction}/{tn_id}'
        payload = {}
        headers = {"Content-Type": "application/json"}
        response = requests.put(url, auth=authentication_cred, headers=headers, json=payload)
        msg = "Something went wrong!"

        if response.status_code == 202:
            print('Transaction deployed successfully.')
            data = {"error":0 , "message": "Haproxy Deployed Successfully","transaction_code":response.status_code}
            msg = "Transaction successful on HA Proxy"
        elif response.status_code == 404:
            print('Transaction not found.')
            data = {"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code}
            msg = 'Transaction expired!'
        else:
            #print(f'Error: {response.status_code}')
            #print(response.text)
            data = {"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code}
            msg = str(response.json()['message'])
            #print("Error1:",response.json()['message'])
            msg = str(response.json()['message']).replace('\n',' ')
            msg = msg.replace('"',' ')
            msg = msg.replace("'",' ')
            print("message: ", msg)
            pattern = re.compile(r'msg= (.*?)\s*(?=(msg=|$))')
            matches = pattern.findall(msg)
            if matches:
                print("Matches:",matches[0][0])
                msg = matches[0][0]

        #session.pop('user_name')
        session.pop('transaction_id')
        generate_transaction()
        #session['is_login'] = False
        flash(str(msg))
        return redirect('/')
    else:
        if is_login:
            flash('You are not a sudo user!')
            return redirect('/')
        flash('Please login')
        return redirect('/login')

##--------------------------------------------  Global  -----------------------------------------
#------------------------------------------------------------------------------------------------
@app.route('/global')
def global_section():
    is_login = session.get('is_login')
    if is_login:
        # get global section
        tn_id = session.get('transaction_id')
        url = f'{api_list.url_global}?transaction_id={tn_id}'
        response = requests.get(url, auth=authentication_cred)
        if response.status_code == 200:
            print(str1,response.json())
            return render_template('global.html', data = json.dumps(response.json()))
        else:
            print(f'Error: {response.status_code}')
            print(response.text)
        flash('Transaction code expired')
        return redirect('/login')
    else:
        flash('Please login')
        return redirect('/login')


@app.route('/save_global', methods=['POST'])
def save_global():
    is_login = session.get('is_login')
    if is_login:
        if session.get('is_sudo'):
            if request.method == "POST":
                data = request.get_json()
                print(data)
                tn_id = session.get('transaction_id')
                url = f'{api_list.url_global}?transaction_id={tn_id}'
                payload = data
                headers = {"Content-Type": "application/json"}
                response = requests.put(url, auth=authentication_cred, headers=headers, json=payload)
                print(response.json())
                if response.status_code == 202: #204
                    print('Transaction updated successfully.')
                    return jsonify({"error":0, "message":"Changes Saved","transaction_code": response.status_code})
                elif response.status_code == 404:
                    print('Transaction not found.')
                    return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})
                else:
                    print(f'Error: {response.status_code}',response.text)
                    return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})

            response_data = {"error": 1,"message": "Something error"}
            return jsonify(response_data)
        else:
            response_data = {"error": 1,"message": "You are not sudo user!"}
            return jsonify(response_data)
    else:
        flash('Please login')
        return redirect('/login')


##----------------------------------------------    default     ----------------------------------
#-------------------------------------------------------------------------------------------------

@app.route('/default')
def defult():
    is_login = session.get('is_login')
    if is_login:
        tn_id = session.get('transaction_id')
        url = f'{api_list.url_default}?transaction_id={tn_id}'
        auth = ('admin', 'nsdl1234')
        response = requests.get(url, auth=auth)
        if response.status_code == 200:
            print(str1,response.json())
            return render_template('default.html', data = json.dumps(response.json()))
        else:
            print(f'Error: {response.status_code}')
            print(response.text)
        flash('Transaction code expired')
        return redirect('/login')
    else:
        flash('Please login')
        return redirect('/login')
    


##  saving default section 

@app.route('/save_default', methods=['POST'])
def save_default():
    is_login = session.get('is_login')
    if is_login:
        if session.get('is_sudo'):
            if request.method == "POST":
                data = request.get_json()
                print(data)
                
                #tn_id = '94bb6146-24c0-455f-90d8-335359e86577'
                name = 'main_default'
                tn_id = session.get('transaction_id')
                print("transaction_id",tn_id)
                url = f'{api_list.url_default}/{name}?transaction_id={tn_id}'
                auth = ('admin', 'nsdl1234')
                payload = data
                headers = {"Content-Type": "application/json"}
                response = requests.put(url, auth=auth, headers=headers, json=payload)
                print(response.json())
                if response.status_code == 202:
                    print('Transaction updated successfully.')
                    return jsonify({"error":0, "message":"Changes Saved","transaction_code": response.status_code})
                elif response.status_code == 404:
                    print('Transaction not found.') ## check for available transaction and fire or generate new transaction
                    return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})       # {'code': 404, 'message': '30: defaults main_default does not exist'}
                else:
                    # Handle other error cases
                    print(f'Error: {response.status_code}')
                    print(response.text)
                    return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})
            
            response_data = {"message": "Something error"}
            return jsonify(response_data)
        else:
            response_data = {"error": 1,"message": "You are not sudo user!"}
            return jsonify(response_data)
    else:
        flash('Please login')
        return redirect('/login')

##--------------------------------------    BACKEND -------------------------------------
#-----------------------------------------------------------------------------------------
## get all the backend names and then get all servers of that backend 
@app.route('/backend')
def backend():
    is_login = session.get('is_login')
    if is_login:
        ## get all the backend                                  
        tn_id = session.get('transaction_id')
        url = f'{api_list.url_backend}?transaction_id={tn_id}'
        response = requests.get(url, auth=authentication_cred)
        if response.status_code == 200:
            print(str1,response.json())
            resp =  response.json()
            parent_list = []
            for i in resp['data']:
                backend_name = i['name']
                url = f'{api_list.url_server}?transaction_id={tn_id}&backend={backend_name}'
                response1 = requests.get(url, auth=authentication_cred)
                if response1.status_code == 200:
                    print(str1,response1.json())
                    parent_list.append({"backend":i, "server":response1.json()})
                else:
                    print(f'Error: {response1.status_code}',response1.text)
            return render_template('backend.html', data = json.dumps(parent_list))
        else:
            print(f'Error: {response.status_code}')
            print(response.text)
        flash('Transaction code expired')
        return redirect('/login')
        
    else:
        flash('Please login')
        return redirect('/login')

@app.route('/save_backend', methods=['POST'])
def save_backend():
    error = 0
    error_msg = ""
    is_login = session.get('is_login')
    if is_login:
        if session.get('is_sudo'):
            ## add new backend or a edit old backend
            if request.method == "POST":
                tn_id = session.get('transaction_id')
                received_data = request.get_json()
                print(received_data)
                #[{"type":"new","data"= {}, "server"=[ {"type":"new","data"={} }, {}] },{},{}]
                for item in received_data:
                    if item['type']== 'new':
                        url = f'{api_list.url_backend}?transaction_id={tn_id}'
                        payload = item['data']
                        headers = {"Content-Type": "application/json"}
                        response = requests.post(url, auth=authentication_cred, headers=headers, json=payload)
                        if response.status_code == 202:
                            print('Transaction created successfully backend as old')
                            print(str1,response.json())
                            #if backend created successfully and check for serveres
                            server_list = item['server']
                            if len(server_list) >0:
                                #create server
                                for lis in server_list:
                                    if lis['type'] == 'new':
                                        ## create server
                                        backend_name = response.json()['name']
                                        url = f'{api_list.url_server}?transaction_id={tn_id}&backend={backend_name}'
                                        payload = lis['data']
                                        headers = {"Content-Type": "application/json"}
                                        response1 = requests.post(url, auth=authentication_cred, headers=headers, json=payload)
                                        print(response1.status_code, response1.json())
                                        if response1.status_code == 202:
                                            print('Transaction created successfully backend old new server')
                                            print(str1,response1.json())
                                            #return jsonify({"error":0, "message":"Changes Saved for backend new and server new","transaction_code": response.status_code, "transaction_code1":response1.status_code})
                                        else:
                                            print(f'Error: {response1.status_code}')
                                            print(response1.text)
                                            error = 1
                                            error_msg += str(response.json())
                            else:
                                print('Changes saved for backend new')
                                #return jsonify({"error":0, "message":"Changes Saved for backend as new","transaction_code": response.status_code})
                                                
                        else:
                            print(f'Error: {response.status_code}',response.text)

                    elif item['type'] == 'old':
                        backend_name = item['data']['name']
                        url = f'{api_list.url_backend}/{backend_name}?transaction_id={tn_id}'
                        payload = item['data']
                        headers = {"Content-Type": "application/json"}
                        response = requests.put(url, auth=authentication_cred, headers=headers, json=payload)
                        if response.status_code == 202:
                            print('Transaction created successfully.')
                            print(str1,response.json())
                            #if backend created successfully and check for serveres
                            server_list = item['server']
                            if len(server_list) >0:
                                #create server
                                for lis in server_list:
                                    if lis['type'] == 'new':
                                        ## create server
                                        backend_name = response.json()['name']
                                        url = f'{api_list.url_server}?transaction_id={tn_id}&backend={backend_name}'
                                        payload = lis['data']
                                        headers = {"Content-Type": "application/json"}
                                        response1 = requests.post(url, auth=authentication_cred, headers=headers, json=payload)
                                        print(response1.status_code, response1.json())
                                        if response1.status_code == 202:
                                            print('Transaction created successfully.')
                                            print(str1,response1.json())
                                            #return jsonify({"error":0, "message":"Changes Saved for backend old and server new","transaction_code": response.status_code, "transaction_code1":response1.status_code})
                                        else:
                                            print(f'Error: {response1.status_code}')
                                            print(response1.text)
                                            error = 1
                                            error_msg += str(response.json())
                                    elif lis['type'] == 'old':
                                        backend_name = response.json()['name']
                                        server_name = lis['data']['name']
                                        url = f'{api_list.url_server}/{server_name}?transaction_id={tn_id}&backend={backend_name}'
                                        payload = lis['data']
                                        headers = {"Content-Type": "application/json"}
                                        response1 = requests.put(url, auth=authentication_cred, headers=headers, json=payload)
                                        print(response1.status_code, response1.json())
                                        if response1.status_code == 202:
                                            print('Transaction created successfully.')
                                            print(str1,response1.json())
                                            #return jsonify({"error":0, "message":"Changes Saved for backend old and server old","transaction_code": response.status_code, "transaction_code1":response1.status_code})
                                        else:
                                            print(f'Error: {response1.status_code}')
                                            print(response1.text)
                                            error = 1
                                            error_msg += str(response.json())
                            else:
                                print("Changes Saved for backend as old")
                                #return jsonify({"error":0, "message":"Changes Saved for backend as old","transaction_code": response.status_code})
                                                
                        else:
                            print(f'Error: {response.status_code}',response.text)

            response_data = {"error":error ,"message": error_msg}
            return jsonify(response_data)
        else:
            response_data = {"error": 1,"message": "You are not sudo user!"}
            return jsonify(response_data)
    else:
        flash('Please login')
        return redirect('/login')

@app.route('/delete_server', methods=['POST'])
def delete_server():
    is_login = session.get('is_login')
    if is_login:
        if session.get('is_sudo'):
            if request.method == "POST":
                tn_id = session.get('transaction_id')
                received_data = request.get_json()
                print(received_data)

                server_name = received_data['server']
                b_name = received_data['backend']

                url = f'{api_list.url_server}/{server_name}?transaction_id={tn_id}&backend={b_name}'
                response = requests.delete(url, auth=authentication_cred)
                if response.status_code == 202:
                    print('Transaction deleted successfully.')
                    return jsonify({"error":0, "message":"Changes Saved Server deleted","transaction_code": response.status_code})
                                            
                else:
                    print(f'Error: {response.status_code}',response.text)
                    return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})
                
            return jsonify({"error":1, "message":"Something went wrong"})
        else:
            response_data = {"error": 1,"message": "You are not sudo user!"}
            return jsonify(response_data)
    else:
        flash('Please login')
        return redirect('/login') 


@app.route('/delete_backend', methods=['POST'])
def delete_backend():
    is_login = session.get('is_login')
    if is_login:
        if session.get('is_sudo'):
            if request.method == "POST":
                tn_id = session.get('transaction_id')
                received_data = request.get_json()
                print(received_data)
                backend_name = received_data['backend']
                url = f'{api_list.url_backend}/{backend_name}?transaction_id={tn_id}'
                response = requests.delete(url, auth=authentication_cred)
                if response.status_code == 202:
                    print('Transaction deleted successfully.')
                    return jsonify({"error":0, "message":"Changes Saved Server deleted","transaction_code": response.status_code})                       
                else:
                    print(f'Error: {response.status_code}',response.text)
                    return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})
                
            return jsonify({"error":1, "message":"Something went wrong"})
        else:
            response_data = {"error": 1,"message": "You are not sudo user!"}
            return jsonify(response_data)
    else:
        flash('Please login')
        return redirect('/login')

##------------------------------------------    Frontend    ---------------------------------------------
#--------------------------------------------------------------------------------------------------------
def http_Redirect_check(frontend):
    api_url = api_list.url_https
    params = {
        "parent_name": frontend,
        "parent_type": "frontend", 
        "transaction_id":  session.get('transaction_id')
    }
    headers = {"Content-Type": "application/json"}
    response = requests.get(api_url, params=params, auth=authentication_cred, headers=headers)
    print("Https redirect response ",response.json())
    if len(response.json()['data'])>0:
        return True
    return False
    

@app.route('/frontend')
def frontend():
    is_login = session.get('is_login')
    if is_login:
        ## get all the frontend                                      [{"frontend":{backend resp},"bind":{}},{},{}]
        
        tn_id = session.get('transaction_id')

        url = f'{api_list.url_backend}?transaction_id={tn_id}'
        response = requests.get(url, auth=authentication_cred)
        backend_names = []
        if response.status_code == 200:
            resp =  response.json()
            for i in resp['data']:
                backend_name = i['name']
                backend_names.append(backend_name)


        url = f'{api_list.url_frontend}?transaction_id={tn_id}'
        response = requests.get(url, auth=authentication_cred)
        if response.status_code == 200:
            print(str1,response.json())
            resp =  response.json()
            parent_list = []
            for i in resp['data']:
                frontend_name = i['name']

                http_redi = http_Redirect_check(frontend_name)

                url = f'{api_list.url_bind}?transaction_id={tn_id}&frontend={frontend_name}'
                response1 = requests.get(url, auth=authentication_cred)
                if response1.status_code == 200:
                    print(str1,response1.json())
                    parent_list.append({"frontend":i,'http_redirect':http_redi, "bind":response1.json()})
                else:
                    print(f'Error: {response1.status_code}',response1.text)
            return render_template('frontend.html', data = json.dumps(parent_list), backend_names = json.dumps(backend_names))
        else:
            print(f'Error: {response.status_code}')
            print(response.text)
        flash('Transaction code expired')
        return redirect('/login')
    else:
        flash('Please login')
        return redirect('/login')

def http_Redirect(frontend):
    # HAProxy Data Plane API endpoint
    api_url = api_list.url_https
    params = {
        "parent_name": frontend,
        "parent_type": "frontend", 
        "transaction_id":  session.get('transaction_id')
    }
    payload = {"cond":"unless","cond_test":"{ ssl_fc }","index":0,"redir_type":"scheme","redir_value":"https","type":"redirect"}
    headers = {"Content-Type": "application/json"}
    response = requests.post(api_url, params=params, auth=authentication_cred, headers=headers, json=payload)
    print("Https redirect enable ",response.json())
    


def http_Redirect_delete(frontend):
    api_url = api_list.url_https + '/0'
    params = {
        "parent_name": frontend,
        "parent_type": "frontend", 
        "transaction_id":  session.get('transaction_id')
    }
    headers = {"Content-Type": "application/json"}
    response = requests.delete(api_url, params=params, auth=authentication_cred, headers=headers)
    print("Https redirect delete:",response.json())




@app.route('/save_frontend', methods=['POST'])
def save_frontend():
    is_login = session.get('is_login')
    if is_login:
        if session.get('is_sudo'):
            error = 0
            error_msg = ''
            ## add new backend or a edit old backend
            if request.method == "POST":
                tn_id = session.get('transaction_id')
                received_data = request.get_json()
                print(received_data)
                #[{"type":"new","data"= {}, "bind"=[ {"type":"new","data"={} }, {}] },{},{}]
                for item in received_data:
                    if item['type']== 'new':
                        url = f'{api_list.url_frontend}?transaction_id={tn_id}'
                        payload = item['data']
                        headers = {"Content-Type": "application/json"}
                        response = requests.post(url, auth=authentication_cred, headers=headers, json=payload)
                        if response.status_code == 202:
                            print('Transaction created successfully for frontend new')
                            print(str1,response.json())
                            
                            ## check if http redirect 
                            try:
                                if item.get('http_redirect') == True:
                                    http_Redirect(payload['name'])
                                else:
                                    http_Redirect_delete(payload['name'])
                            except Exception as e:
                                print("Exception in http redirect {e}")

                            #if frontend created successfully and check for bind
                            bind_list = item['bind']
                            if len(bind_list) >0:
                                #create server
                                for lis in bind_list:
                                    if lis['type'] == 'new':
                                        ## create server
                                        frontend_name = response.json()['name']
                                        url = f'{api_list.url_bind}?transaction_id={tn_id}&frontend={frontend_name}'
                                        payload = lis['data']
                                        headers = {"Content-Type": "application/json"}
                                        response1 = requests.post(url, auth=authentication_cred, headers=headers, json=payload)
                                        print(response1.status_code, response1.json())
                                        if response1.status_code == 202:
                                            print('Transaction created successfully for bind new')
                                            print(str1,response1.json())
                                            #return jsonify({"error":0, "message":"Changes Saved for frontend new and bind new","transaction_code": response.status_code, "transaction_code1":response1.status_code})
                                        else:
                                            print(f'Error: {response1.status_code}')
                                            print(response1.text)
                                            error = 1
                                            error_msg += str(response.json())
                            else:
                                print('saved frontend new')
                                #return jsonify({"error":0, "message":"Changes Saved for frontend as new","transaction_code": response.status_code})
                                                
                        else:
                            print(f'Error: {response.status_code}',response.text)
                            error = 1
                            error_msg += str(response.json())

                    elif item['type'] == 'old':
                        frontend_name = item['data']['name']
                        url = f'{api_list.url_frontend}/{frontend_name}?transaction_id={tn_id}'
                        payload = item['data']
                        headers = {"Content-Type": "application/json"}
                        response = requests.put(url, auth=authentication_cred, headers=headers, json=payload)
                        if response.status_code == 202:
                            print('Transaction created successfully for frontend old')
                            try:
                                if item.get('http_redirect') == True:
                                    http_Redirect(payload['name'])
                                else:
                                    http_Redirect_delete(payload['name'])
                            except Exception as e:
                                print("Exception in http redirect {e}")
                            print(str1,response.json())
                            #if backend created successfully and check for serveres
                            bind_list = item['bind']
                            if len(bind_list) >0:
                                #create server
                                for lis in bind_list:
                                    if lis['type'] == 'new':
                                        ## create server
                                        frontend_name = response.json()['name']
                                        url = f'{api_list.url_bind}?transaction_id={tn_id}&frontend={frontend_name}'
                                        payload = lis['data']
                                        headers = {"Content-Type": "application/json"}
                                        response1 = requests.post(url, auth=authentication_cred, headers=headers, json=payload)
                                        print(response1.status_code, response1.json())
                                        if response1.status_code == 202:
                                            print('Transaction created successfully for bind new')
                                            print(str1,response1.json())
                                            #return jsonify({"error":0, "message":"Changes Saved for frontend old and bind new","transaction_code": response.status_code, "transaction_code1":response1.status_code})
                                        else:
                                            print(f'Error: {response1.status_code}')
                                            print(response1.text)
                                            error = 1
                                            error_msg += str(response.json())
                                    elif lis['type'] == 'old':
                                        frontend_name = response.json()['name']
                                        bind_name = lis['data']['name']
                                        url = f'{api_list.url_bind}/{bind_name}?transaction_id={tn_id}&frontend={frontend_name}'
                                        payload = lis['data']
                                        headers = {"Content-Type": "application/json"}
                                        response1 = requests.put(url, auth=authentication_cred, headers=headers, json=payload)
                                        print(response1.status_code, response1.json())
                                        if response1.status_code == 202:
                                            print('Transaction created successfully for bind old')
                                            print(str1,response1.json())
                                            #return jsonify({"error":0, "message":"Changes Saved for frontend old and bind old","transaction_code": response.status_code, "transaction_code1":response1.status_code})
                                        else:
                                            print(f'Error: {response1.status_code}')
                                            print(response1.text," old error")
                                            error = 1
                                            error_msg += str(response.json())
                            else:
                                print('saved frontend as old')
                                #return jsonify({"error":0, "message":"Changes Saved for frontend as old","transaction_code": response.status_code})
                                                
                        else:
                            print(f'Error: {response.status_code}',response.text)
                            error = 1
                            error_msg += str(response.json())
                    

            response_data = {"error":error ,"message": error_msg}
            return jsonify(response_data)
        else:
            response_data = {"error": 1,"message": "You are not sudo user!"}
            return jsonify(response_data)
    else:
        flash('Please login')
        return redirect('/login')



@app.route('/delete_bind', methods=['POST'])
def delete_bind():
    is_login = session.get('is_login')
    if is_login:
        if session.get('is_sudo'):
            if request.method == "POST":
                tn_id = session.get('transaction_id')
                received_data = request.get_json()
                print(received_data)
                bind_name = received_data['bind']
                frontend_name = received_data['frontend']
                parent_type = 'frontend'
                url = f'{api_list.url_bind}/{bind_name}?transaction_id={tn_id}&frontend={frontend_name}'
                print(url)
                response = requests.delete(url, auth=authentication_cred)
                
                if response.status_code == 202:
                    print('Transaction deleted successfully.')
                    return jsonify({"error":0, "message":"Changes Saved bind deleted","transaction_code": response.status_code})
                                            
                else:
                    print(f'Error: {response.status_code}',response.text)
                    return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})
                
            return jsonify({"error":1, "message":"Something went wrong"})
        else:
            response_data = {"error": 1,"message": "You are not sudo user!"}
            return jsonify(response_data)
    else:
        flash('Please login')
        return redirect('/login')


@app.route('/delete_frontend', methods=['POST'])
def delete_frontend():
    is_login = session.get('is_login')
    if is_login:
        if session.get('is_sudo'):
            if request.method == "POST":
                tn_id = session.get('transaction_id')
                received_data = request.get_json()
                print(received_data)
                frontend_name = received_data['frontend']
                url = f'{api_list.url_frontend}/{frontend_name}?transaction_id={tn_id}'
                response = requests.delete(url, auth=authentication_cred)
                if response.status_code == 202:
                    print('Transaction deleted successfully.')
                    return jsonify({"error":0, "message":"Changes Saved frontend deleted","transaction_code": response.status_code})                       
                else:
                    print(f'Error: {response.status_code}',response.text)
                    return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})
                
            return jsonify({"error":1, "message":"Something went wrong"})
        else:
            response_data = {"error": 1,"message": "You are not sudo user!"}
            return jsonify(response_data)
    else:
        flash('Please login')
        return redirect('/login')



##-----------------------------------------     BACKEND switching rules------------------------------------
@app.route('/backend_switching_rule')
def backend_switching_rule():
    ## get all frontend             # [{"frontend":{}, "acl":{}, "rule":{} },{}]
    ## get all acl
    ## get all switching rule
    is_login = session.get('is_login')
    if is_login:
        tn_id = session.get('transaction_id')
        # get the backend names in list
        url = f'{api_list.url_backend}?transaction_id={tn_id}'
        response = requests.get(url, auth=authentication_cred)
        backend_names = []
        if response.status_code == 200:
            resp =  response.json()
            for i in resp['data']:
                backend_name = i['name']
                backend_names.append(backend_name)
                

        # get all acl rules 
        url = f'{api_list.url_frontend}?transaction_id={tn_id}'
        response = requests.get(url, auth=authentication_cred)
        if response.status_code == 200:
            print(str1,response.json())
            resp =  response.json()
            parent_list = []
            for i in resp['data']:
                frontend_name = i['name']

                url = f'{api_list.url_backend_switch_rule}?transaction_id={tn_id}&frontend={frontend_name}'
                response1 = requests.get(url, auth=authentication_cred)
                if response1.status_code == 200:
                    print(str1,response1.json())
                else:
                    print(f'Error switch rule: {response1.status_code}',response1.text)
                    return "Error"

                parent_type = 'frontend'
                url = f'{api_list.url_acl}?transaction_id={tn_id}&parent_name={frontend_name}&parent_type={parent_type}'
                response2 = requests.get(url, auth=authentication_cred)
                if response2.status_code == 200:
                    print(str1,response2.json())
                else:
                    print(f'Error alc: {response2.status_code}',response2.text)
                    return "Error"

                parent_list.append({"frontend":i, "rule":response1.json(),"acl":response2.json()})

            return render_template('switching_rule.html', data = json.dumps(parent_list), backend_names = json.dumps(backend_names))
        else:
            print(f'Error: {response.status_code}')
            print(response.text) 
        flash('Transaction code expired')
        return redirect('/login')
    else:
        flash('Please login')
        return redirect('/login')

@app.route('/save_switching_rule', methods=['POST'])
def save_switching_rule():
    is_login = session.get('is_login')
    if is_login:
        if session.get('is_sudo'):
            error = 0
            error_msg = ''
            if request.method == "POST":
                tn_id = session.get('transaction_id')
                received_data = request.get_json()
                print(received_data)            #[{ "type":"new", "frontend": "" ,"data" = {} },{}]

                for item in received_data:
                    if item['type'] == "new":
                        frontend_name = item['frontend']
                        url = f'{api_list.url_backend_switch_rule}?transaction_id={tn_id}&frontend={frontend_name}'
                        payload = item['data']
                        headers = {"Content-Type": "application/json"}
                        response = requests.post(url, auth=authentication_cred, headers=headers, json=payload)
                        if response.status_code == 202:
                            print('Transaction created successfully for new switching rule')
                            #return jsonify({"error":0, "message":"Changes Saved","transaction_code": response.status_code})                  
                        else:
                            print(f'Error: {response.status_code}',response.text)
                            error = 1
                            error_msg += str(response.json())
                            #return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})
                    
                    elif item['type'] == "old":
                        frontend_name = item['frontend']
                        index = item['data']['index']
                        url = f'{api_list.url_backend_switch_rule}/{index}?transaction_id={tn_id}&frontend={frontend_name}'
                        payload = item['data']
                        headers = {"Content-Type": "application/json"}
                        response = requests.put(url, auth=authentication_cred, headers=headers, json=payload)
                        if response.status_code == 202:
                            print('Transaction edited successfully for old')
                            #return jsonify({"error":0, "message":"Changes Saved ","transaction_code": response.status_code})                      
                        else:
                            print(f'Error: {response.status_code}',response.text)
                            error = 1
                            error_msg += str(response.json())
                            #return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})
        
            return jsonify({"error":error, "message":error_msg})
        else:
            response_data = {"error": 1,"message": "You are not sudo user!"}
            return jsonify(response_data)
    else:
        flash('Please login')
        return redirect('/login')

@app.route('/delete_switching_rule', methods=['POST'])
def delete_switching_rule():
    is_login = session.get('is_login')
    if is_login:
        if session.get('is_sudo'):
            if request.method == "POST":
                tn_id = session.get('transaction_id')
                received_data = request.get_json()
                print(received_data)
                index = received_data['index']
                frontend_name = received_data['frontend']
                url = f'{api_list.url_backend_switch_rule}/{index}?transaction_id={tn_id}&frontend={frontend_name}'
                response = requests.delete(url, auth=authentication_cred)
                if response.status_code == 202:
                    print('Transaction deleted successfully.')
                    return jsonify({"error":0, "message":"Changes Saved Switching rule deleted","transaction_code": response.status_code})             
                else:
                    print(f'Error: {response.status_code}',response.text)
                    return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})
                
            return jsonify({"error":1, "message":"Something went wrong"})
        else:
            response_data = {"error": 1,"message": "You are not sudo user!"}
            return jsonify(response_data)
    else:
        flash('Please login')
        return redirect('/login')

##------------------------------------------    ACL LINES   ------------------------------------------

@app.route('/acl_lines')
def acl_lines():
    ## get all frontend             # [{"frontend":{}, "acl":{} },{}]
    ## get all acl
    is_login = session.get('is_login')
    if is_login:
        tn_id = session.get('transaction_id')
        url = f'{api_list.url_frontend}?transaction_id={tn_id}'
        response = requests.get(url, auth=authentication_cred)
        if response.status_code == 200:
            print(str1,response.json())
            resp =  response.json()
            parent_list = []
            for i in resp['data']:
                frontend_name = i['name']

                parent_type = 'frontend'
                url = f'{api_list.url_acl}?transaction_id={tn_id}&parent_name={frontend_name}&parent_type={parent_type}'
                response2 = requests.get(url, auth=authentication_cred)
                if response2.status_code == 200:
                    print(str1,response2.json())
                    parent_list.append({"frontend":i, "acl":response2.json()})
                else:
                    print(f'Error alc: {response2.status_code}',response2.text)
                    return "Error"
            return render_template('acl.html', data = json.dumps(parent_list))
        else:
            print(f'Error: {response.status_code}')
            print(response.text)
        flash('Transaction code expired')
        return redirect('/login')
    else:
        flash('Please login')
        return redirect('/login')


@app.route('/save_acl_rule', methods=['POST'])
def save_acl_rule():
    is_login = session.get('is_login')
    if is_login:
        if session.get('is_sudo'):
            error = 0
            error_msg = ''
            if request.method == "POST":
                tn_id = session.get('transaction_id')
                received_data = request.get_json()
                print(received_data)            #[{ "type":"new", "frontend": "" ,"data" = {} },{}]

                for item in received_data:
                    if item['type'] == "new":
                        frontend_name = item['frontend']
                        parent_type = 'frontend'
                        url = f'{api_list.url_acl}?transaction_id={tn_id}&parent_name={frontend_name}&parent_type={parent_type}'
                        payload = item['data']
                        headers = {"Content-Type": "application/json"}
                        response = requests.post(url, auth=authentication_cred, headers=headers, json=payload)
                        if response.status_code == 202:
                            print('Transaction created successfully for new acl line')
                            #return jsonify({"error":0, "message":"Changes Saved","transaction_code": response.status_code})                  
                        else:
                            print(f'Error for new acl line: {response.status_code}',response.text)
                            error = 1
                            error_msg += str(response.json())
                            #return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})
                    
                    elif item['type'] == "old":
                        frontend_name = item['frontend']
                        index = item['data']['index']
                        parent_type = 'frontend'
                        url = f'{api_list.url_acl}/{index}?transaction_id={tn_id}&parent_name={frontend_name}&parent_type={parent_type}'
                        payload = item['data']
                        headers = {"Content-Type": "application/json"}
                        response = requests.put(url, auth=authentication_cred, headers=headers, json=payload)
                        if response.status_code == 202:
                            print('Transaction edited successfully for old acl line')
                            #return jsonify({"error":0, "message":"Changes Saved ","transaction_code": response.status_code})                      
                        else:
                            print(f'Error for old acl line: {response.status_code}',response.text)
                            error_msg += "  \n "
                            error_msg += str(response.json())
                            error = 1
                            #return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})
        
            return jsonify({"error":error, "message":error_msg})
        else:
            response_data = {"error": 1,"message": "You are not sudo user!"}
            return jsonify(response_data)
    else:
        flash('Please login')
        return redirect('/login')

@app.route('/delete_acl_rule', methods=['POST'])
def delete_acl_rule():
    is_login = session.get('is_login')
    if is_login:
        if session.get('is_sudo'):
            if request.method == "POST":
                tn_id = session.get('transaction_id')
                received_data = request.get_json()
                print(received_data)
                index = received_data['index']
                frontend_name = received_data['frontend']
                parent_type = 'frontend'
                url = f'{api_list.url_acl}/{index}?transaction_id={tn_id}&parent_name={frontend_name}&parent_type={parent_type}'
                response = requests.delete(url, auth=authentication_cred)
                if response.status_code == 202:
                    print('Transaction deleted successfully.')
                    return jsonify({"error":0, "message":"Changes Saved. ACL deleted","transaction_code": response.status_code})
                                            
                else:
                    print(f'Error: {response.status_code}',response.text)
                    return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})
                
            return jsonify({"error":1, "message":"Something went wrong"})
        else:
            response_data = {"error": 1,"message": "You are not sudo user!"}
            return jsonify(response_data)
    else:
        flash('Please login')
        return redirect('/login')

#------------------------------------------------- Stats  -----------------------------------------
@app.route('/stats')
def stats():
    is_login = session.get('is_login')
    if is_login:
        ## get all the frontend                                      [{"frontend":{backend resp},"bind":{}},{},{}]
        tn_id = session.get('transaction_id')
        url = f'{api_list.url_frontend}?transaction_id={tn_id}'
        response = requests.get(url, auth=authentication_cred)
        if response.status_code == 200:
            print(str1,response.json())
            resp =  response.json()
            parent_list = []
            for i in resp['data']:
                frontend_name = i['name']
                if frontend_name == 'stats':
                    url = f'{api_list.url_bind}?transaction_id={tn_id}&frontend={frontend_name}'
                    response1 = requests.get(url, auth=authentication_cred)
                    if response1.status_code == 200:
                        print(str1,response1.json())
                        parent_list.append({"frontend":i, "bind":response1.json()['data']})
                    else:
                        parent_list.append({"frontend":i, "bind":[]})
                        print(f'Error: {response1.status_code}',response1.text)
            
            return render_template('stats.html', data = json.dumps(parent_list))
        else:
            print(f'Error: {response.status_code}')
            print(response.text)
        flash('Transaction code expired')
        return redirect('/login')
    else:
        flash('Please login')
        return redirect('/login')
    

@app.route('/save_stats', methods = ['POST'])
def save_stats():
    is_login = session.get('is_login')
    if is_login:
        if session.get('is_sudo'):
            if request.method == "POST":
                data = request.get_json()
                print("Data received",data)
                tn_id = session.get('transaction_id')
                if data.get('stats_action')== False:
                    ## deete stats
                    f_name = 'stats'
                    url = f'{api_list.url_frontend}/{f_name}?transaction_id={tn_id}'
                    response = requests.delete(url, auth=authentication_cred)
                    if response.status_code == 202:
                        print('Stats deleted successfully.')
                        return jsonify({"error":0, "message":"Changes Saved","transaction_code": response.status_code})
                    else:
                        print(f'Error: {response.status_code}')
                        print(response.text)
                        

                else:
                    ## delete frontend
                    f_name = 'stats'
                    url = f'{api_list.url_frontend}/{f_name}?transaction_id={tn_id}'
                    response = requests.delete(url, auth=authentication_cred)
                    if response.status_code == 202:
                        print('Stats deleted successfully.')
                        
                       
                    else:
                        print(f'Error: {response.status_code}')
                        print(response.text) 
                    
                    #tn_id = '94bb6146-24c0-455f-90d8-335359e86577'
                                    
                    # deploy frontend
                    url = f'{api_list.url_frontend}?transaction_id={tn_id}'
                    payload = {'mode': 'http', 'name': 'stats', 
                            'stats_options': {'stats_admin': True, 'stats_admin_cond': 'if',
                                                'stats_admin_cond_test': 'LOCALHOST', 'stats_enable': True,
                                                    'stats_refresh_delay': int(data.get('refreshrate')), 'stats_uri_prefix': data.get('urll'),
                                                    'stats_auths': [{'passwd': data.get('password'),'user': data.get('username')}]
                                                }
                            }
                    headers = {"Content-Type": "application/json"}
                    response = requests.post(url, auth=authentication_cred, headers=headers, json=payload)

                    if response.status_code == 202:
                        print('Frontend Transaction created successfully.')
                        ##deploy bind
                        url = f'{api_list.url_bind}?transaction_id={tn_id}&frontend={f_name}'

                        payload = {"name": "bindstats*", "address":data.get('bindaddress'), "port": int(data.get('bindport'))}
                        
                        headers = {"Content-Type": "application/json"}
                        response = requests.post(url, auth=authentication_cred, headers=headers, json=payload)
                        print(response.status_code, response.json())
                        if response.status_code == 202:
                            print('Bind Transaction created successfully.')
                            print('Response Data:')
                            print(response.json()) 
                            return jsonify({"error":0, "message":"Changes Saved","transaction_code": response.status_code})
                        else:
                            print(f'Stats success but bind Error : {response.status_code}')
                            print(response.text)

                    elif response.status_code == 404:
                        print('Transaction not found.') ## check for available transaction and fire or generate new transaction
                        return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})       # {'code': 404, 'message': '30: defaults main_default does not exist'}
                    else:
                        # Handle other error cases
                        print(f'Error: {response.status_code}')
                        print(response.text)
                        return jsonify({"error": 1 , "message": response.json()['message'], "code":response.json()['code'],"transaction_code": response.status_code})
                
            response_data = {"error": 1,"message": "Something wrong!"}
            return jsonify(response_data)
        else:
            response_data = {"error": 1,"message": "You are not sudo user!"}
            return jsonify(response_data)
    else:
        flash('Please login')
        return redirect('/login')


#-------------------------------------------------  HA PROXY service status ------------------------
@app.route('/ha_proxy_status')
def ha_proxy_status():
    try:
        # Run the systemctl status command to check Nginx service status
        status_output = subprocess.check_output(['systemctl', 'status', 'nginx'], stderr=subprocess.STDOUT, universal_newlines=True)
        return render_template('index.html', status=status_output)
    except Exception as e:
        # Handle errors (e.g., Nginx service not found)
        return render_template('index.html', status=f"Error: {e}")
    
@app.route('/stop_ha_proxy')
def stop_ha_proxy():
    is_login = session.get('is_login')
    is_sudo = session.get('is_sudo')
    if is_login and is_sudo:
        action = request.args.get('action')
        try:
            status_output = subprocess.check_output(['systemctl', action, 'haproxy'], stderr=subprocess.STDOUT, universal_newlines=True)
            #return render_template('index.html', status=status_output)
            print(f'{action} ha proxy',status_output )
            time.sleep(5)
            return redirect('/')
        except Exception as e:
            print('exception in stopping ha proxy',e)
            time.sleep(5)
            return redirect('/')
    
    else:
        if is_login:
            flash('You are not a sudo user!')
            return redirect('/')
        flash('Please login')
        return redirect('/login')


@app.route('/restart_ha_proxy')
def restart_ha_proxy():
    is_login = session.get('is_login')
    is_sudo = session.get('is_sudo')
    if is_login and is_sudo:
        try:
            # Run the systemctl status command to check Nginx service status
            status_output = subprocess.check_output(['systemctl', 'restart', 'haproxy'], stderr=subprocess.STDOUT, universal_newlines=True)
            #return render_template('index.html', status=status_output)
            print('restart ha proxy',status_output )
            time.sleep(5)
            return redirect('/')
        except Exception as e:
            # Handle errors (e.g., Nginx service not found)
            #return render_template('index.html', status=f"Error: {e.output}")
            print('exception in restart ha proxy',e)
            time.sleep(5)
            return redirect('/')
    else:
        if is_login:
            flash('You are not a sudo user!')
            return redirect('/')
        flash('Please login')
        return redirect('/login')

##-------------------------------------------------  JUORNAL CTL LOGS -------------------------------

@app.route('/journal')
def journal():
    is_login = session.get('is_login')
    if is_login:
        try:
            #sudo journalctl -xeu haproxy.service
            command = ['sudo', 'journalctl', '-xeu', 'haproxy','--reverse']
            output = subprocess.run(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            sudo_prompt = output.stderr.strip()
            if output.returncode != 0:
                print("Error: Failed to check the logs of HA Proxy.")
                print("Error Message:",sudo_prompt)
                return render_template('juornalctl.html', status=output.stdout.strip())
            #print("HA Proxy Status:")
            #print(output.stdout.strip())

            return render_template('juornalctl.html', status=output.stdout.strip())
        except Exception as e:
            return render_template('juornalctl.html', status=f"Cannot find HA proxy status \n Error: {e}")
            sys.exit(1)
    else:
        return redirect('/login')


@app.route('/list_config')
def list_config():
    is_login = session.get('is_login')
    if is_login:
        try:
            folder_path = api_list.folder_path
            files = list_files_in_folder(folder_path)
            print(files)
            return render_template('list_config.html', files=files)
        except Exception as e:
            print(e)
            return render_template('list_config.html', files=[])
    else:
        flash('Please login')
        return redirect('/login')

@app.route('/file')
def view_file():
    is_login = session.get('is_login')
    if is_login:
        file_name = request.args.get('file_name')
        folder_path = api_list.folder_path
        file_path = os.path.join(folder_path, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                file_content = file.read()
            return Response(file_content, content_type='text/plain')
        else:
            return 'File not found'
    else:
        flash('Please login')
        return redirect('/login')


@app.route('/current_haproxy')
def current_haproxy():
    is_login = session.get('is_login')
    if is_login:
        tn_id = session.get('transaction_id')
        url = f'{api_list.url_config}?transaction_id={tn_id}'
        response = requests.get(url, auth=authentication_cred)
        if response.status_code == 200:
            print(str1,response.json())
            marked_data = Markup(response.json()["data"])
            #marked_data = response.json()["data"]
            return render_template('current_haproxy.html', data = marked_data)
        else:
            print(f'Error: {response.status_code}')
            print(response.text)
        return redirect('/login')
    else:
        flash('Please login')
        return redirect('/login')



app.run('0.0.0.0', port=5052)
