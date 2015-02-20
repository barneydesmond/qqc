--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: plpgsql; Type: PROCEDURAL LANGUAGE; Schema: -; Owner: postgres
--

CREATE PROCEDURAL LANGUAGE plpgsql;


ALTER PROCEDURAL LANGUAGE plpgsql OWNER TO postgres;

SET search_path = public, pg_catalog;

--
-- Name: clear_error(integer); Type: FUNCTION; Schema: public; Owner: qqc_quartett
--

CREATE FUNCTION clear_error(integer) RETURNS void
    AS $_$DECLARE
  eid ALIAS FOR $1;
BEGIN
  UPDATE "errors" SET "fixed_flag"=TRUE WHERE "error_id"=eid;
  RETURN;
END;$_$
    LANGUAGE plpgsql STRICT;


ALTER FUNCTION public.clear_error(integer) OWNER TO qqc_quartett;

--
-- Name: report_error(text, text, text, text, text); Type: FUNCTION; Schema: public; Owner: qqc_quartett
--

CREATE FUNCTION report_error(text, text, text, text, text) RETURNS void
    AS $_$DECLARE
  script_name ALIAS FOR $1;
  line_num ALIAS FOR $2;
  proofreader ALIAS FOR $3;
  description ALIAS FOR $4;
  filename ALIAS FOR $5;
BEGIN
  INSERT INTO errors VALUES (default, script_name, line_num, proofreader, description, filename, false);
  RETURN;
END;$_$
    LANGUAGE plpgsql;


ALTER FUNCTION public.report_error(text, text, text, text, text) OWNER TO qqc_quartett;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: errors; Type: TABLE; Schema: public; Owner: qqc_quartett; Tablespace: 
--

CREATE TABLE errors (
    error_id integer NOT NULL,
    script_name text DEFAULT 'NO_FILE'::text NOT NULL,
    linenum text NOT NULL,
    proofreader text DEFAULT 'Anonymous'::text NOT NULL,
    description text DEFAULT 'NO_ERROR'::text NOT NULL,
    img_filename text,
    fixed_flag boolean DEFAULT false NOT NULL
);


ALTER TABLE public.errors OWNER TO qqc_quartett;

--
-- Name: errors_error_id_seq; Type: SEQUENCE; Schema: public; Owner: qqc_quartett
--

CREATE SEQUENCE errors_error_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.errors_error_id_seq OWNER TO qqc_quartett;

--
-- Name: errors_error_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qqc_quartett
--

ALTER SEQUENCE errors_error_id_seq OWNED BY errors.error_id;


--
-- Name: errors_error_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qqc_quartett
--

SELECT pg_catalog.setval('errors_error_id_seq', 252, true);


--
-- Name: lines; Type: TABLE; Schema: public; Owner: qqc_quartett; Tablespace: 
--

CREATE TABLE lines (
    script_name text NOT NULL,
    linenum text NOT NULL,
    otext text,
    ttext text,
    speaker text,
    comment text
);


ALTER TABLE public.lines OWNER TO qqc_quartett;

--
-- Name: proofreaders; Type: TABLE; Schema: public; Owner: qqc_quartett; Tablespace: 
--

CREATE TABLE proofreaders (
    name text NOT NULL,
    privileged boolean DEFAULT false NOT NULL
);


ALTER TABLE public.proofreaders OWNER TO qqc_quartett;

--
-- Name: COLUMN proofreaders.privileged; Type: COMMENT; Schema: public; Owner: qqc_quartett
--

COMMENT ON COLUMN proofreaders.privileged IS 'Determines whether the proofreader has ability to dismiss reports and whatnot';


--
-- Name: error_id; Type: DEFAULT; Schema: public; Owner: qqc_quartett
--

ALTER TABLE errors ALTER COLUMN error_id SET DEFAULT nextval('errors_error_id_seq'::regclass);


--
-- Data for Name: errors; Type: TABLE DATA; Schema: public; Owner: qqc_quartett
--

COPY errors (error_id, script_name, linenum, proofreader, description, img_filename, fixed_flag) FROM stdin;
3	10010930.qml	331	furinkan	more headroom on the right	\N	f
10	20030604.qml	276	furinkan	There's an image-text around here. Sensei is holding up one finger, and there's a 'pi' (hiragana) next to it.	\N	f
19	4B032203.qml	625	AstCd2	Line assigned to May instead of Juni	\N	f
22	3C031002.qml	366	AstCd2	Klarissa's lines here are assigned to Juni	\N	f
23	4C999901.qml	408	AstCd2	This is Charl's line	\N	f
30	4A0319E2b.qml	89	furinkan	missing a word or two	\N	t
58	4A032206.qml	158	furinkan	Furi: reflow this line	\N	f
5	10021503.qml	195	furinkan	I'd -> I ?	\N	t
6	10022105.qml	133	furinkan	should be more of a "Yes! I'm coming~!"?	\N	t
7	10022107.qml	182	furinkan	"bagatelle" might be a nice substitute for "play on words"	\N	t
9	20030605.qml	257	furinkan	reword this line to include the concept that her talent is fiery/wild/etc. and that she hasn't been "utilised" yet	\N	t
11	20030703.qml	299	furinkan	Has he executed a particular set of steps? I expect what he really meant was to stir things up, in which case, "I've already done what needed to be done" or something, would be appropriate.	\N	t
16	30031008.qml	445	furinkan	damn or damned?	\N	t
14	30031008.qml	445	furinkan	next line starts with ellipsis, should use ellipsis instead of lines to follow-on?	\N	t
15	30031008.qml	556	furinkan	suggest "Shut it!", as the next line starts with "listen up", two 'up's might sound weird.	\N	t
12	3A031002.qml	162	furinkan	gratuitous? more like "unnecessary" perhaps? I assume he's referring to the extra attention he's getting.	\N	t
13	3A031004.qml	60	furinkan	"he and you", somewhat awkward	\N	t
24	3A0311E1.qml	498	furinkan	upswelling or upwelling?	\N	t
53	3A0311E1.qml	553	furinkan	capitalise "Sir", I think.	\N	t
25	3A0311E2.qml	435	furinkan	found another instance of sensei	\N	t
17	3A0316E1.qml	472	furinkan	I know we voted on this, but I still vote member->erection as a better term.	\N	t
18	3A0316E1.qml	717	furinkan	I'm not entirely the hydrodynamic behaviour described here is anatomically possible. Request a minor rewording, maybe removing a small detail.	\N	t
61	40032302.qml	106	furinkan	I assume it's the entry to the competition, I don't know if "luggage" is the right word. Maybe bag/bags/briefcase/belongings/personal effects.	\N	t
27	4A0319E1.qml	145	furinkan	Split onto two lines? All previous ero has sound effects on their own line.	\N	t
32	4A0319E2a.qml	87	furinkan	"...! Mmn...!" makes for a weird line. Drop the start?	\N	t
33	4A0319E2a.qml	93	furinkan	separate line for sound effect?	\N	t
34	4A0319E2a.qml	153	furinkan	remove leading ellipsis?	\N	t
28	4A0319E2b.qml	79	furinkan	remove beginning ellipsis?	\N	t
29	4A0319E2b.qml	82	furinkan	remove beginning ellipsis?	\N	t
31	4A0319E2b.qml	89	furinkan	a word or two too-many/too-few, suggest maybe "She whispers in a stunned voice, her entire face bathed in white"	\N	t
37	4A0319E3.qml	187	furinkan	Is it really that torrential? I was thinking something slightly more subtle, maybe "seeps out and runs down her thighs"	\N	t
35	4A0319E3.qml	221	furinkan	weird structure again with leading ellipsis	\N	t
36	4A0319E3.qml	254	furinkan	line must be incorrect, she just went down on him, not the other way around.	\N	t
41	4A0319E4.qml	120	furinkan	suggest "honey-moistened crevasse" -> "moist lips". I think there's an excess of honey appearing in this scene.	\N	t
42	4A0319E4.qml	173	furinkan	doubled-ampersand is a typo, but how many periods should be there?	\N	t
43	4A0319E4.qml	181	furinkan	there's a lot of constricting going on, suggest "flesh quivers in time"	\N	t
44	4A0319E4.qml	327	furinkan	suggest "until it can't go any further/deeper."	\N	t
45	4A0319E4.qml	489	furinkan	bottom? buttocks perhaps?	\N	t
48	4A0319E4.qml	514	furinkan	suggest "from our connection" -> "from where we are joined"	\N	t
51	4A0319E4.qml	709	furinkan	remove ellipsis or move them to before an exclamation mark	\N	t
46	4A0319E4.qml	883	furinkan	suggest expunged->expended	\N	t
47	4A0319E4.qml	915	furinkan	suggest crevasse->opening	\N	t
3C0310E1.qml	221	0/0/俺の舌の動きに合わせて..<BR>淑花も反応を返してくれる<BR>夜のレッスン室に<BR>二人の舌を絡ませる音が響く	0/0/She begins to respond&, matching the movements<BR>of my tongue&... The sound of our entwined tongues<BR>echoes throughout the night-time classroom&.	Etc	
\.


--
-- Data for Name: proofreaders; Type: TABLE DATA; Schema: public; Owner: qqc_quartett
--

COPY proofreaders (name, privileged) FROM stdin;
furinkan	t
AstCd2	t
USERNAME_ERROR	f
\.


--
-- Name: errors_pkey; Type: CONSTRAINT; Schema: public; Owner: qqc_quartett; Tablespace: 
--

ALTER TABLE ONLY errors
    ADD CONSTRAINT errors_pkey PRIMARY KEY (error_id);


--
-- Name: lines_pkey; Type: CONSTRAINT; Schema: public; Owner: qqc_quartett; Tablespace: 
--

ALTER TABLE ONLY lines
    ADD CONSTRAINT lines_pkey PRIMARY KEY (script_name, linenum);


--
-- Name: proofreaders_pkey; Type: CONSTRAINT; Schema: public; Owner: qqc_quartett; Tablespace: 
--

ALTER TABLE ONLY proofreaders
    ADD CONSTRAINT proofreaders_pkey PRIMARY KEY (name);


--
-- Name: script_name_idx; Type: INDEX; Schema: public; Owner: qqc_quartett; Tablespace: 
--

CREATE INDEX script_name_idx ON lines USING btree (script_name);


--
-- Name: errors_proofreader_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qqc_quartett
--

ALTER TABLE ONLY errors
    ADD CONSTRAINT errors_proofreader_fkey FOREIGN KEY (proofreader) REFERENCES proofreaders(name) ON UPDATE CASCADE ON DELETE SET DEFAULT;


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

