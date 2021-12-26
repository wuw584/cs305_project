**Pclient registers a file**

```
            REGISTER
            Fid
            File Length
            Upload Rate
                =>
Pclient                   Tracker
                <=
         REGISTER SUCCESS
```

**Pclient registers a window in file**

```
         REGISTER WIN
         Fid
         Win
         Upload Rate
              =>      
Pclient                Tracker
              <=
       REGISTER SUCCESS
```

**Pclient wants to download a window in file**

```
            QUERY
            Fid
            Win
             =>
Pclient                Tracker
             <=
          Peer List
```

**Pclient queries the length of file**

```
        QUERYLENGTH
        Fid
             =>
Pclient                Tracker
             <=
         File Length
```

**Pclient cancels a file**

```
            CANCEL
            Fid
             =>
Pclient                Tracker
             <=
        CANCEL SUCCESS
```

**Pclient closes**

```
            CLOSE
             =>
Pclient                Tracker
             <=
        CLOSE SUCCESS
```

**Pclient downloads a seg in file from another Pclient**

```
           QUERY
           Fid
           seg
             =>
Pclient                Pclient
             <=
           RETURN
           seg
           seg's data
```


