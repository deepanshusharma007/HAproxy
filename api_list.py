server_ip = '10.101.104.140:5555'

url_version = f'http://{server_ip}/v2/services/haproxy/configuration/version'

url_check_transaction = f'http://{server_ip}/v2/services/haproxy/transactions'

url_default = f'http://{server_ip}/v2/services/haproxy/configuration/named_defaults'

url_global = f'http://{server_ip}/v2/services/haproxy/configuration/global'

url_backend = f'http://{server_ip}/v2/services/haproxy/configuration/backends'

url_server = f'http://{server_ip}/v2/services/haproxy/configuration/servers'

url_frontend = f'http://{server_ip}/v2/services/haproxy/configuration/frontends'

url_bind = f'http://{server_ip}/v2/services/haproxy/configuration/binds'

url_backend_switch_rule = f'http://{server_ip}/v2/services/haproxy/configuration/backend_switching_rules'

url_acl = f'http://{server_ip}/v2/services/haproxy/configuration/acls'

url_config = f'http://{server_ip}/v2/services/haproxy/configuration/raw'

url_https = f'http://{server_ip}/v2/services/haproxy/configuration/http_request_rules'

folder_path = "/home/ipmcloud/old_haproxy/"
