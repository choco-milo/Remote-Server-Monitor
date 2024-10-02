import pandas as pd 
import paramiko
from io import StringIO
import socket

def connect_to_server(hostname, port, username, password, commands):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=hostname, port=port, username=username, password=password, timeout=10)
        
        outputs = []
        for c in commands:
            stdin, stdout, stderr = client.exec_command(c)
            output = stdout.read().decode()
            outputs.append(output.strip())
        client.close()
        return outputs

    except paramiko.AuthenticationException:
        return "Wrong password"
    except (paramiko.SSHException, socket.timeout) as e:
        return f"Connection error: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def parse_df_output(output):
    try:
        df = pd.read_csv(StringIO(output), sep='\s+')
        return df
    except pd.errors.EmptyDataError:
        return None
    except Exception as e:
        print(f"Error parsing output: {e}")
        return None

def process_servers(servers_df):
    results = []
    commands = [
        "df -h --total", 
        "mpstat 1 1 | awk 'NR==4{print 100-$12}'",
        "free -h | awk 'NR==2{print ($3/$2)*100}'"
    ]

    for index, row in servers_df.iterrows():
        hostname = row['servers']
        port = row['port']
        username = row['username']
        password = row['password']
        
        result = connect_to_server(hostname, port, username, password, commands)
        
        if isinstance(result, str):  # If the result is an error message
            print(f"Failed to connect to {hostname}: {result}")
            continue  # Skip to the next server
        
        df = parse_df_output(result[0])
        if df is not None and not df.empty:
            try:
                disk_usage = df.iloc[-1]["Use%"] if "Use%" in df.columns else 'N/A'
                cpu = result[1] + '%'
                ram_usage = result[2].strip() + '%'

                results.append({
                    'hostname': hostname,
                    'username': username,
                    'disk_usage': disk_usage,
                    'cpu': cpu,
                    'RAM': ram_usage
                })
            except Exception as e:
                print(f"Error processing data from {hostname}: {e}")
        else:
            print(f"Invalid output from {hostname}, skipping.")

    return results
