Final Turn: Append the to `/workspace/run.sh`, so that we can call it later:

```
bash$(get_alias_cmd) $(get_target_command)="$(get_replacement)"
```
