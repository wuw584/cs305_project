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

```
            QUERY
            Fid
            Win
             =>
Pclient                Tracker
             <=
          Peer List
```

```
        QUERYLENGTH
        Fid
             =>
Pclient                Tracker
             <=
         File Length
```

```
            CANCEL
            Fid
             =>
Pclient                Tracker
             <=
        CANCEL SUCCESS
```

```
            CLOSE
             =>
Pclient                Tracker
             <=
        CLOSE SUCCESS
```


