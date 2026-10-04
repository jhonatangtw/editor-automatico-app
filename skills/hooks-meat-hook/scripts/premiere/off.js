var p=app.project,root=p.rootItem,hooks=null,r=[];
for(var j=0;j<root.children.numItems;j++) if(root.children[j].name=="HOOKS") hooks=root.children[j];
for(var k=0;k<hooks.children.numItems;k++){ var b=hooks.children[k]; for(var i=0;i<b.children.numItems;i++){ var it=b.children[i];
  if(it.type==1 && it.isOffline()) r.push(b.name+"/"+it.name+" -> "+it.getMediaPath()); } }
return "offline: "+r.length+"\n"+r.join("\n");
