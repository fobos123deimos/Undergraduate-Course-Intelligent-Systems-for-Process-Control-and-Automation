function members=throttle_zip_members(path)
%THROTTLE_ZIP_MEMBERS Validate classic ZIP structure without extracting files.
% Portable to MATLAB and Octave without Java or external executables. ZIP64,
% multipart and non-UTF8 extended filenames are explicitly unsupported.
fid=fopen(path,'rb');assert(fid>=0,'Cannot open ZIP source');
bytes=fread(fid,Inf,'*uint8');fclose(fid);n=numel(bytes);
assert(n>=22,'Invalid ZIP: truncated source');
eocd=0;
for p=n-21:-1:max(1,n-65556)
 if isequal(bytes(p:p+3),uint8([80;75;5;6])) && p+21+u16(bytes,p+20)==n
  eocd=p;break;
 end
end
assert(eocd>0,'Invalid ZIP: central-directory end record missing');
assert(u16(bytes,eocd+4)==0 && u16(bytes,eocd+6)==0,'Multipart ZIP is unsupported');
entries=u16(bytes,eocd+10);size_cd=u32(bytes,eocd+12);offset_cd=u32(bytes,eocd+16);
assert(entries==u16(bytes,eocd+8) && entries<65535 && ...
 size_cd<4294967295 && offset_cd<4294967295,'Multipart or ZIP64 source is unsupported');
assert(offset_cd+size_cd<=eocd-1,'Invalid ZIP: central directory extends beyond archive');
p=offset_cd+1;limit=p+size_cd;members=cell(1,entries);
for j=1:entries
 assert(p+45<limit && isequal(bytes(p:p+3),uint8([80;75;1;2])), ...
  'Invalid ZIP: malformed central-directory entry');
 flags=u16(bytes,p+8);compressed=u32(bytes,p+20);
 name_length=u16(bytes,p+28);extra_length=u16(bytes,p+30);comment_length=u16(bytes,p+32);
 local=u32(bytes,p+42)+1;next=p+46+name_length+extra_length+comment_length;
 assert(name_length>0 && next<=limit && u16(bytes,p+34)==0,'Invalid ZIP entry bounds');
 assert(compressed<4294967295 && local<4294967296,'ZIP64 source is unsupported');
 name=bytes(p+46:p+45+name_length)';
 if bitand(uint16(flags),uint16(2048))
  members{j}=native2unicode(name,'UTF-8');
 else
  assert(all(name<128),'Non-UTF8 extended ZIP filenames are unsupported');
  members{j}=char(name);
 end
 assert(local>=1 && local+29<=offset_cd && isequal(bytes(local:local+3),uint8([80;75;3;4])), ...
  'Invalid ZIP: local entry header missing');
 local_name=u16(bytes,local+26);local_extra=u16(bytes,local+28);
 payload=local+30+local_name+local_extra;
 assert(payload+compressed-1<=offset_cd && local_name==name_length, ...
  'Invalid ZIP: local entry extends into central directory');
 assert(isequal(bytes(local+30:local+29+local_name)',name),'Invalid ZIP: inconsistent member names');
 p=next;
end
assert(p==limit,'Invalid ZIP: central-directory size mismatch');
end

function value=u16(bytes,p)
value=double(bytes(p))+256*double(bytes(p+1));
end

function value=u32(bytes,p)
value=double(bytes(p))+256*double(bytes(p+1))+65536*double(bytes(p+2))+16777216*double(bytes(p+3));
end
