from socket import *
import os
import sys
import struct
import time
import select
import binascii

#default valuse set from start
ICMP_ECHO_REQUEST = 8
MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 1
# The packet that we shall send to each router along the path is the ICMP echo
# request packet, which is exactly what we had used in the ICMP ping exercise.
# We shall use the same packet that we built in the Ping exercise

def checksum(string):
# In this function we make the checksum of our packet
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum += thisVal
        csum &= 0xffffffff
        count += 2

    if countTo < len(string):
        csum += (string[len(string) - 1])
        csum &= 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def build_packet():
    #Fill in start
    # In the sendOnePing() method of the ICMP Ping exercise ,firstly the header of our
    # packet to be sent was made, secondly the checksum was appended to the header and
    # then finally the complete packet was sent to the destination.
    myID = os.getpid() & 0xFFFF  # Return the current process id
    #Need PID to populate the struct
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, 0, myID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    # Make the header in a similar way to the ping exercise. Copied from ping lab.
    # Append checksum to the header.
    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network  byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    # Don’t send the packet yet , just return the final packet in this function.
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, myID, 1)
    #Fill in end

    # So the function ending should look like this

    packet = header + data
    return packet

def get_route(hostname):
    destAddr = gethostbyname(hostname)
    timeLeft = TIMEOUT
    tracelist1 = [] #This is your list to use when iterating through each trace
    tracelist2 = [] #This is your list to contain all traces

    for ttl in range(1,MAX_HOPS):
        for tries in range(TRIES):
            destAddr = gethostbyname(hostname)

            #Fill in start
            # Make a raw socket named mySocket
            # Pull in from Pinger Lab
            icmp = getprotobyname("icmp")
            mySocket = socket(AF_INET, SOCK_RAW, icmp)
            mySocket.bind(("", 0))
            #mySocket.close() #try me
            #Fill in end

            mySocket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))
            mySocket.settimeout(TIMEOUT)
            try:
                d = build_packet()
                mySocket.sendto(d, (hostname, 0))
                t = time.time()
                startedSelect = time.time()
                whatReady = select.select([mySocket], [], [], timeLeft)
                howLongInSelect = (time.time() - startedSelect)
                if whatReady[0] == []: # Timeout
                    tracelist1.append("* * * Request timed out.")
                    #Fill in start
                    #You should add the list above to your all traces list
                    tracelist2.append([str(ttl), "*", "Request timed out"])
                    #Fill in end
                recvPacket, addr = mySocket.recvfrom(1024)
                timeReceived = time.time()
                timeLeft = timeLeft - howLongInSelect
                if timeLeft <= 0:
                    tracelist1.append("* * * Request timed out.")
                    #Fill in start
                    #You should add the list above to your all traces list
                    tracelist2.append([str(ttl), "*", "Request timed out"])
                    #Fill in end
            except timeout:
                continue

            else:
                #Fill in start
                #Fetch the icmp type from the IP packet
                types, Code, Checksum, packetid, Sequence = struct.unpack('bbHHh', recvPacket[20:28])
                #Fill in end
                try: #try to fetch the hostname
                    #Fill in start
                    hostname_try = gethostbyaddr(addr[0])
                    #Fill in end
                except herror as e:   #if the host does not provide a hostname
                    #Fill in start
                    hostname_try = 'hostname not returnable'
                    #Fill in end
                if isinstance(hostname_try, tuple):
                    hostname_try = hostname_try[0]

                if types == 11:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    #Fill in start
                    #You should add your responses to your lists here
                    delay = timeReceived - t
                    delay = round(delay * 1000)
                    delay_as_string = str(delay) + "ms"
                    #need to diff between IP address and URI
                    tracelist2.append([str(ttl), delay_as_string, addr[0], hostname_try])
                    #Fill in end
                    print('{}\t{}\t{}\t{}'.format(str(ttl), delay_as_string, addr[0], hostname_try))
                elif types == 3:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    #Fill in start
                    #You should add your responses to your lists here
                    delay = timeReceived - t
                    delay = round(delay * 1000)
                    delay_as_string = str(delay) + "ms"
                    tracelist2.append([str(ttl), delay_as_string, addr[0], hostname_try])
                    #Fill in end
                    print('{}\t{}\t{}\t{}'.format(str(ttl), delay_as_string, addr[0], hostname_try))
                elif types == 0:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    #Fill in start
                    #You should add your responses to your lists here and return your list if your destination IP is met
                    delay = timeReceived - timeSent
                    delay = round(delay * 1000)
                    delay_as_string = str(delay) + "ms"
                    tracelist2.append([str(ttl), delay_as_string, addr[0], hostname_try])
                    return tracelist2 #used at end to return a value for none
                    # Fill in end
                    print('{}\t{}\t{}\t{}'.format(str(ttl), delay_as_string, addr[0], hostname_try))
                else:
                    #Fill in start
                    #If there is an exception/error to your if statements, you should append that to your list here
                    tracelist2.append([str(ttl), '*', 'Request timed out'])
                    print('{}\t{}\t{}\t{}'.format(str(ttl), '*', 'Request timed out'))
                    #Fill in end
                break
            finally:
                mySocket.close()

if __name__ == '__main__':
    get_route("www.bing.com")
