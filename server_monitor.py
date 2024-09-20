import pandas as pd 
import paramiko
from io import StringIO




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
    except Exception as e:
        return str(e)




def parse_df_output(output):
    df = pd.read_csv(StringIO(output),  sep='\s+')
    return df









if __name__ == "__main__":
    servers_df = pd.read_excel('input2.xlsx')
    results = []
    
    # Commands
    commands = ["df -h --total", 
            "mpstat 1 1 | awk 'NR==4{print  100-$12}'",
            "free -h | awk 'NR==2{print ($3/$2)*100}'"
                ]

    for index, row in servers_df.iterrows():
        hostname = row['servers']
        port = row['port']
        username = row['username']
        password = row['password']
        result = connect_to_server(hostname, port, username, password, commands)
        



        if result == "Wrong password":
            print(f"Failed to connect to {hostname}: {result}")
        else:   
            df = parse_df_output(result[0])
            disk_usage = df.iloc[-1]["Use%"]
            total_capacity = result[1].strip()+'%'
            ram_usage = result[2].strip()+'%'

            results.append({
                'hostname': hostname,
                'total_size': disk_usage,
                'capacity': total_capacity,
                'RAM': ram_usage
            })
                


    final_results_df = pd.DataFrame(results)
    final_results_df.to_csv('output.csv', index=False)




