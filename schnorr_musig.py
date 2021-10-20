import schnorr_lib as sl
import sys, getopt, json
from binascii import hexlify, unhexlify 

def main(argv):

    msg = "messaggio da firmare"
    # msg_bytes = sl.hash_sha256(msg.encode()) # va effettuato l'hash? 
    msg_bytes = msg.encode()

    # Get keypairs
    keypairs = json.load(open("keypairs.json", "r"))
    
    l = b''
    for x in keypairs["keypairs"]:
        l += sl.pubkey_gen_from_hex(x["privateKey"])
    L = sl.hash_sha256(l)

    Psum = None
    Rsum = None
    X = None
    for x in keypairs["keypairs"]:
        di = x["privateKey"]
        #Pi = sl.pubkey_gen_from_hex(di)
        Pi = sl.pubkey_point_gen_from_int(sl.int_from_bytes(unhexlify(di)))

        if Psum == None:
            Psum = Pi
        else:
            Psum = sl.point_add(Psum, Pi)
        
        # va bene generare k così? 
        t = sl.xor_bytes(unhexlify(di), sl.tagged_hash("BIP340/aux", sl.get_aux_rand()))
        ki = sl.int_from_bytes(sl.tagged_hash("BIP340/nonce", t + sl.bytes_from_point(Pi) + msg_bytes)) % sl.n
        if ki == 0:
            raise RuntimeError('Failure. This happens only with negligible probability.')
        x["ki"] = ki

        Ri = sl.point_mul(sl.G, ki)
        if Ri == None:
            Rsum = Ri
        else:
            Rsum = sl.point_add(Rsum, Ri)

        # bi = h(L||Pi), dove L = h(P1||..||Pn)
        bi = sl.int_from_bytes(sl.hash_sha256(L + sl.bytes_from_point(Pi)))
        x["bi"] = bi

        xi = sl.point_mul(Pi, bi)
        if X == None:
            X = xi
        else:
            X = sl.point_add(X, xi)

    e_ = sl.int_from_bytes(sl.hash_sha256(sl.bytes_from_point(X) + sl.bytes_from_point(Rsum) + msg_bytes))
    
    ssum = 0
    for x in keypairs["keypairs"]:
        di = sl.int_from_bytes(unhexlify(x["privateKey"]))
        ei = e_ * x["bi"]
        si = x["ki"] + di + ei % sl.n
        ssum += si
    
    ssum = ssum % sl.n
    
    print(">>> Then the sign is (Rsum,ssum)")

    # VERIFICATION

    Rv = sl.point_mul(sl.G, ssum)
    other = sl.point_mul(X, e_)
    sumv = sl.point_add(Rsum, other)

    # print("Rv = ssum*G =",Rv)
    # print("Rsum + e'*X =", Rsum, "+", other, "=", sum)
    print(">>> Is the sign right? (Rv equals Rsum + e'*X)?", Rv == sumv)
    print(Rv)
    print()
    print(sumv)

if __name__ == "__main__":
   main(sys.argv[1:])
