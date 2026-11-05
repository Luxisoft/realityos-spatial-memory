import React from 'react';
import {AbsoluteFill, Audio, Composition, Freeze, Img, OffthreadVideo, Sequence, getInputProps, interpolate, registerRoot, staticFile, useCurrentFrame} from 'remotion';

type Clip = {asset: string; start: number; length: number};
type Scene = {id: string; start: number; duration: number; kind: string; title: string; eyebrow: string; body: string; audio: string; audio_duration: number; captions: {text:string;start:number;end:number}[]; clips: Clip[]};
type Props = {duration: number; variant: string; scenes: Scene[]};
const C = {bg:'#10161d', panel:'#1a232e', line:'#334354', blue:'#8bc5fa', text:'#f4f6f8', muted:'#afbdca'};
const font = 'Reality Sans, Arial, sans-serif';

const Fade: React.FC<{children:React.ReactNode}> = ({children}) => {
  const f=useCurrentFrame();
  const opacity=interpolate(f,[0,12],[0,1],{extrapolateRight:'clamp'});
  return <div style={{opacity,transform:`translateY(${interpolate(f,[0,18],[12,0],{extrapolateRight:'clamp'})}px)`}}>{children}</div>;
};
const Tag:React.FC<{children:React.ReactNode}> = ({children}) => <span style={{display:'inline-block',padding:'10px 16px',border:`1px solid ${C.line}`,borderRadius:8,fontSize:19,color:C.blue,letterSpacing:1.3,fontWeight:600}}>{children}</span>;

function Footage({clips, duration, style={}}:{clips:Clip[];duration:number;style?:React.CSSProperties}) {
  let cursor=0;
  const segments=clips.map((clip,i)=>{
    const from=cursor;cursor+=Math.round(clip.length*30);
    return <Sequence key={i} from={from} durationInFrames={Math.round(clip.length*30)} layout="none">
      <OffthreadVideo src={staticFile(`media/${clip.asset}.mp4`)} startFrom={Math.round(clip.start*30)} muted style={{width:'100%',height:'100%',objectFit:'contain',...style}} />
    </Sequence>;
  });
  const last=clips[clips.length-1];
  return <AbsoluteFill style={{overflow:'hidden',background:'#10161d'}}>{segments}{cursor<duration*30 && last ? <Sequence from={cursor} durationInFrames={duration*30-cursor} layout="none"><Freeze frame={Math.max(0,Math.round(last.length*30)-2)}><OffthreadVideo src={staticFile(`media/${last.asset}.mp4`)} startFrom={Math.round(last.start*30)} muted style={{width:'100%',height:'100%',objectFit:'contain',...style}} /></Freeze></Sequence>:null}</AbsoluteFill>;
}

function Phone({scene}:{scene:Scene}){
  const isDisplay=scene.kind==='display'||scene.kind==='hook';
  return <div style={{position:'absolute',right:isDisplay?158:196,top:132,width:348,height:774,borderRadius:23,border:`2px solid ${C.line}`,overflow:'hidden',boxShadow:'0 20px 65px #0009',background:'#111'}}>
    <Footage clips={scene.clips} duration={scene.duration}/>
  </div>;
}

function Stats(){return <div style={{display:'flex',gap:28,marginTop:46}}>{[['16','CASE RECORDS'],['5','ACTIVE WARRANTS'],['4','SEARCH ORDERS']].map(([n,t])=><div key={n} style={{borderTop:`2px solid ${C.blue}`,paddingTop:14,width:208}}><div style={{fontSize:62,fontWeight:700}}>{n}</div><div style={{fontSize:16,color:C.muted,letterSpacing:1.1,marginTop:5}}>{t}</div></div>)}</div>}

function RecordSteps({scene}:{scene:Scene}){
 const f=useCurrentFrame();
 const active=f<210?0:f<680?1:2;
 return <div style={{marginTop:38,width:640}}>{['Attach a photo + ask a question','Review the returned records','Open the case information'].map((s,i)=><div key={s} style={{display:'flex',alignItems:'center',gap:18,padding:'17px 0',borderBottom:`1px solid ${C.line}`,opacity:active===i?1:.53}}><span style={{fontSize:19,fontWeight:700,color:active===i?C.blue:C.muted}}>0{i+1}</span><span style={{fontSize:25}}>{s}</span></div>)}<div style={{marginTop:28,fontSize:21,color:C.muted,lineHeight:1.4}}>Candidate records require review.<br/>Case status comes from stored records.</div></div>;
}

function ModelArchitecture(){
 const f=useCurrentFrame();
 return <div style={{position:'absolute',left:780,right:86,top:196}}>{[
 ['01','MUSE SPARK','Visual requests + contextual reasoning','providers / meta'],
 ['02','SAM 3.1','Object segmentation + visual evidence','processing / segmentation'],
 ['03','MUSE VOICE TRANSCRIBE','Speech → a searchable request','providers / transcription'],
 ].map(([n,name,role,code],i)=><div key={n} style={{display:'flex',gap:24,padding:'26px 28px',border:`1px solid ${C.line}`,borderRadius:16,background:C.panel,marginBottom:18,opacity:interpolate(f,[i*12,i*12+14],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}}><span style={{fontSize:21,color:C.blue,marginTop:4}}>{n}</span><div><div style={{fontSize:29,fontWeight:700}}>{name}</div><div style={{fontSize:23,marginTop:9,color:C.muted}}>{role}</div><div style={{fontSize:17,marginTop:14,color:C.blue,fontFamily:'monospace'}}>{code}</div></div></div>)}<div style={{fontSize:21,lineHeight:1.5,color:C.muted,padding:'12px 5px'}}>Face comparison: independent component<br/>Workspace permissions · Consent gates · Original evidence</div></div>;
}

function Contributions(){return <div style={{position:'absolute',left:796,right:95,top:206}}>
 <div style={{color:C.muted,fontSize:20,letterSpacing:2,marginBottom:20}}>OCT 27 — NOV 4, 2026</div>
 {['Video support + segmentation refinements','Android + glasses interaction workflows','Authorized profiles + linked case records'].map((x,i)=><div key={x} style={{padding:'25px 24px',borderLeft:`3px solid ${C.blue}`,background:C.panel,marginBottom:18,fontSize:29,lineHeight:1.3}}><span style={{display:'block',fontSize:17,color:C.blue,marginBottom:8}}>CONTRIBUTION 0{i+1}</span>{x}</div>)}
 <div style={{fontSize:22,color:C.muted,lineHeight:1.5,marginTop:24}}>Built on an existing foundation.<br/>Contribution history available in the public repository.</div>
 </div>}

function Concepts({duration}:{duration:number}){
 return <div style={{position:'absolute',left:760,right:80,top:165,display:'flex',gap:24}}>{[
 {asset:'nursing_concept',label:'CARE WORKFLOWS',desc:'Authorized information',start:2.8,length:1.5},
 {asset:'memory_concept',label:'EVERYDAY MEMORY',desc:'Where an object was last seen',start:10.7,length:5.5}
 ].map(v=><div key={v.asset} style={{width:490}}><div style={{position:'relative',height:594,overflow:'hidden',borderRadius:18,border:`1px solid ${C.line}`}}><Footage clips={[{asset:v.asset,start:v.start,length:v.length}]} duration={duration}/></div><div style={{fontSize:20,color:C.blue,letterSpacing:1.3,marginTop:20}}>{v.label}</div><div style={{fontSize:22,color:C.muted,marginTop:8}}>{v.desc}</div></div>)}</div>;
}

function IntroConcepts({duration}:{duration:number}){
 return <div style={{position:'absolute',left:824,top:180,display:'flex',gap:22}}>{[{asset:'police_concept',start:0,length:5.5},{asset:'social_concept',start:0,length:8.3}].map((v,i)=><div key={v.asset} style={{width:440}}><div style={{position:'relative',height:620,borderRadius:20,overflow:'hidden',border:`1px solid ${C.line}`}}><Footage clips={[v]} duration={duration}/></div><div style={{fontSize:21,color:C.blue,marginTop:22,letterSpacing:1.1}}>{i===0?'PUBLIC SAFETY':'SOCIAL CONNECTIONS'}</div><div style={{fontSize:17,color:C.muted,marginTop:8}}>AI-generated use-case illustration</div></div>)}</div>;
}

function SceneView({scene,index,total,duration}:{scene:Scene;index:number;total:number;duration:number}){
 const f=useCurrentFrame();
 const caption=scene.captions.find(c=>f/30>=c.start&&f/30<c.end);
 const technical=scene.kind==='models'||scene.kind==='contributions'||scene.kind==='concepts';
 const titleSize=scene.kind==='hook'?98:technical?73:78;
 const label=scene.kind==='display'?'SIMULATED META DISPLAY PREVIEW':scene.kind==='police'||scene.kind==='policeauth'?'LOCAL EVALUATION · CASE RECORDS':scene.kind==='socialauth'?'LOCAL EVALUATION · SOCIAL CONNECTION':scene.kind==='models'?'IMPLEMENTED META INTEGRATIONS':scene.kind==='concepts'?'ADDITIONAL USE-CASE CONCEPTS':'';
 return <AbsoluteFill style={{background:C.bg,fontFamily:font,color:C.text}}>
  <style>{`@font-face{font-family:'Reality Sans';src:url('${staticFile('font-regular.ttf')}')}@font-face{font-family:'Reality Sans';font-weight:700;src:url('${staticFile('font-bold.ttf')}')}`}</style>
  <AbsoluteFill style={{backgroundImage:'linear-gradient(#8bc5fa06 1px,transparent 1px),linear-gradient(90deg,#8bc5fa06 1px,transparent 1px)',backgroundSize:'96px 96px',opacity:.5}}/>
  <div style={{position:'absolute',left:76,top:44,display:'flex',alignItems:'center',gap:14}}><Img src={staticFile('icon_app.png')} style={{width:44,height:44,borderRadius:'50%'}}/><div style={{fontSize:25,fontWeight:700,letterSpacing:2}}>REALITYOS</div></div>
  <div style={{position:'absolute',right:80,top:58,fontSize:17,color:C.muted,letterSpacing:2}}>BUILD FOR YOUR WORLD <span style={{marginLeft:34,color:C.blue}}>{String(index+1).padStart(2,'0')} / {String(total).padStart(2,'0')}</span></div>
  <div style={{position:'absolute',left:76,top:115,width:1768,height:1,background:C.line}}/>
  {scene.kind==='closing'?<>
   <div style={{position:'absolute',top:190,left:130,right:130,textAlign:'center'}}><Img src={staticFile('icon_app.png')} style={{width:112,height:112,borderRadius:'50%',marginBottom:30}}/><div style={{fontSize:95,fontWeight:700,letterSpacing:-3}}>Your world. Within reach.</div><div style={{fontSize:37,color:C.muted,marginTop:28}}>What would you build with RealityOS?</div><div style={{display:'flex',justifyContent:'center',gap:20,marginTop:44}}><Tag>JOSE MARIN</Tag><Tag>INDIE DEVELOPER</Tag><Tag>OPEN SOURCE</Tag></div><div style={{fontSize:27,color:C.blue,marginTop:43}}>github.com/Luxisoft/realityos-spatial-memory</div></div>
  </>:<>
   <div style={{position:'absolute',left:76,top:197,width:technical?630:690}}><Fade>
    <div style={{fontSize:19,color:C.blue,letterSpacing:3,fontWeight:700,marginBottom:24}}>{scene.eyebrow}</div>
    <div style={{fontSize:titleSize,fontWeight:700,letterSpacing:-2.5,lineHeight:1.04,whiteSpace:'pre-line'}}>{scene.title}</div>
    <div style={{marginTop:30,fontSize:28,lineHeight:1.45,color:C.muted,whiteSpace:'pre-line'}}>{scene.body}</div>
    {scene.kind==='policeauth'?<Stats/>:null}
    {scene.kind==='police'?<RecordSteps scene={scene}/>:null}
    {scene.kind==='hook'?<div style={{marginTop:46,display:'flex',gap:14}}><Tag>ANDROID APP</Tag><Tag>META AI</Tag></div>:null}
    {scene.kind==='overview'?<div style={{marginTop:50,fontSize:25,color:C.text}}>José Marín <span style={{color:C.muted}}> / Solo builder</span></div>:null}
    {scene.kind==='socialauth'?<div style={{marginTop:40}}><Tag>SIMULATED SOCIAL CONNECTION</Tag><div style={{fontSize:22,color:C.muted,marginTop:20}}>Separate accounts. Shared group context.</div></div>:null}
    {scene.kind==='display'?<div style={{marginTop:42,display:'flex',flexDirection:'column',gap:18,fontSize:25}}>{['01  Choose person search','02  Capture a reference portrait','03  Open the authorized profile'].map(t=><div key={t} style={{paddingBottom:17,borderBottom:`1px solid ${C.line}`}}>{t}</div>)}</div>:null}
    {scene.kind==='models'?<div style={{fontSize:22,lineHeight:1.5,color:C.muted,marginTop:40}}>Visual understanding.<br/>Structured context.<br/>Evidence you can inspect.</div>:null}
   </Fade></div>
   {['hook','policeauth','police','socialauth','display'].includes(scene.kind)?<Phone scene={scene}/>:null}
   {scene.kind==='police'&&f>210?<div style={{position:'absolute',left:830,top:250,width:470}}><div style={{fontSize:18,color:C.blue,letterSpacing:2,marginBottom:16}}>RECORDED APP DETAIL</div><Img src={staticFile(`media/${f<780?'police-response':'police-record'}.jpg`)} style={{width:470,maxHeight:540,objectFit:'contain',objectPosition:'top',border:`1px solid ${C.line}`,borderRadius:12}}/></div>:null}
   {scene.kind==='display'&&f>600?<div style={{position:'absolute',left:870,top:250,width:390}}><div style={{fontSize:18,color:C.blue,letterSpacing:2,marginBottom:16}}>AUTHORIZED PROFILE</div><Img src={staticFile('media/social-profile.jpg')} style={{width:390,maxHeight:540,objectFit:'contain',objectPosition:'top',border:`1px solid ${C.line}`,borderRadius:12}}/></div>:null}
   {scene.kind==='overview'?<IntroConcepts duration={scene.duration}/>:null}
   {scene.kind==='models'?<ModelArchitecture/>:null}
   {scene.kind==='contributions'?<Contributions/>:null}
   {scene.kind==='concepts'?<Concepts duration={scene.duration}/>:null}
  </>}
  {label?<div style={{position:'absolute',left:76,bottom:170,fontSize:16,letterSpacing:1.8,color:C.blue}}>{label}</div>:null}
  <div style={{position:'absolute',bottom:0,left:0,right:0,height:140,background:'#0b1017',borderTop:`1px solid ${C.line}`,display:'flex',alignItems:'center',justifyContent:'center',padding:'20px 110px',boxSizing:'border-box'}}><div style={{textAlign:'center',fontSize:33,lineHeight:1.3,maxWidth:1640,color:'#fff'}}>{caption?.text??''}</div></div>
  <div style={{position:'absolute',bottom:0,left:0,height:4,width:`${(scene.start+f/30)/duration*100}%`,maxWidth:'100%',background:C.blue,opacity:.65}}/>
  <Audio src={staticFile(scene.audio)} volume={1}/>
 </AbsoluteFill>;
}

const Film:React.FC<Props> = (props)=><AbsoluteFill>{props.scenes.map((scene,i)=><Sequence key={scene.id} from={Math.round(scene.start*30)} durationInFrames={Math.round(scene.duration*30)}><SceneView scene={scene} index={i} total={props.scenes.length} duration={props.duration}/></Sequence>)}</AbsoluteFill>;
const Root=()=>{
 const props=getInputProps() as unknown as Props;
 return <Composition id="RealityOS" component={Film} durationInFrames={Math.round((props.duration||180)*30)} width={1920} height={1080} fps={30} defaultProps={props}/>;
};
registerRoot(Root);
