def log(location, message):
  # print location, message
  pass

header_size = 8

def recv_bytes(socket, total_bytes):
  data_buffer = ""
  current_bytes = len(data_buffer)
  while current_bytes != total_bytes:
    log("recv_bytes", "Current bytes: " + str(current_bytes) + "Total bytes: " + str(total_bytes))
    new_text = socket.recv(total_bytes - current_bytes)
    data_buffer = data_buffer + new_text
    current_bytes = len(data_buffer)
  return data_buffer

###Header size is the number of bytes to get header
def recv_message(socket):
  num_bytes = int(recv_bytes(socket, header_size))
  log('recv_message', "recieving message")
  message = recv_bytes(socket, num_bytes)
  log('recv_message', message)
  return message

def message_size(message):
  len_mess = str(len(message))
  while len(len_mess) < header_size:
      len_mess = '0' + len_mess
  return len_mess

def send_bytes(socket, data_buffer):
  sent_bytes = 0
  total_bytes = len(data_buffer)
  #log('send_bytes', total_bytes)
  while sent_bytes < total_bytes:
    #log('send_bytes', "data_buffer: >" + data_buffer + "<")
    sent = socket.send(data_buffer)
    #log('send_bytes', "sent: " + str(sent))
    sent_bytes += sent
    #log('send_bytes', "sent_bytes: " + str(sent_bytes))
    data_buffer = data_buffer[sent:len(data_buffer)]

def send_message(socket, message):
  header = message_size(message)
  log(len(message), header)
  message = header + message
  log('send_message', message)
  send_bytes(socket, message)
  #log('send_message', "sent")
